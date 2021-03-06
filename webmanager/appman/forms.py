from appman.models import *
from django.forms import *
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.flatpages.models import FlatPage

class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ('name',)


class ApplicationForm(ModelForm):
    zipfile = FileField(label="Zip file")
    
    class Meta:
        model = Application
        fields = ('name', 'zipfile','icon','category','description')


class ApplicationAddForm(ApplicationForm):
    tos = BooleanField(label='I agree to the <a href="/tos/">terms of service</a>.',
            required=False) # it is required, but handled below for a custom error message.

    def clean_tos(self):
        tos = self.cleaned_data['tos']
        if not tos:
            raise ValidationError("You have to agree to the Terms of Service.")
	
class ApplicationEditForm(ApplicationForm):
    zipfile = FileField(label="Zip file", required=False)
    icon = ImageField(required=False)
    
    
class DocumentationForm(ModelForm):
    class Meta:
        model = FlatPage
        fields = ('title','content')
        
class ProjectorControlForm(ModelForm):

    def clean(self):
        cleaned_data = self.cleaned_data
        
        startup_week_time = cleaned_data['startup_week_time']
        shutdown_week_time = cleaned_data['shutdown_week_time']
        startup_weekend_time = cleaned_data['startup_weekend_time']
        shutdown_weekend_time = cleaned_data['shutdown_weekend_time']

        if startup_week_time >= shutdown_week_time:
            raise ValidationError("The startup week time time must be lower than the shutdown week time.")
            
        if startup_weekend_time >= shutdown_weekend_time:
            raise ValidationError("The startup weekend time must be lower than the shutdown weekend time.")
            
        return cleaned_data
        
    class Meta:
        model = ProjectorControl
        
class ScreenSaverTimeForm(ModelForm):
    inactivity_time = TimeField(input_formats=['%H:%M:%S'], help_text="Use the format (HH:MM:SS)")
    application = ModelChoiceField(queryset=Application.objects.filter(category=Category.objects.get(name='Screensaver')))
    
    def clean_inactivity_time(self):
        inactivity_time = self.cleaned_data['inactivity_time']
        if str(inactivity_time) == '00:00:00':
            raise forms.ValidationError('Time must be at least 00:01 (one minute).')
        return inactivity_time
    
    class Meta:
        model = ScreensaverControl
        fields = ('inactivity_time','application')
    
class UserCreationForm(ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and password.
    """
    username = RegexField(label=("Username"), max_length=30, regex=r'^\w+$', required=True)
    email = EmailField(label=("Email"), required=True, help_text="(Must be a uc.pt account.)")
    password1 = CharField(label=("Password"), widget=PasswordInput, required=True)
    password2 = CharField(label=("Password confirmation"), widget=PasswordInput, required=True)

    class Meta:
        model = User
        fields = ("username",)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        try:
            User.objects.get(username=username)
            raise ValidationError("Username already taken.")
        except User.DoesNotExist:
            return username

    def clean_password1(self):
        passw = self.cleaned_data['password1'].strip()
        if len(passw) < 6:
            raise ValidationError("Password should have at least 6 characters.")
        return passw

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if email.endswith('uc.pt'):
            return email
        else:
            raise ValidationError("Email must be on uc.pt domain.")
            
    def clean(self):
        cleaned_data = self.cleaned_data


        password1 = cleaned_data.get("password1", "")
        password2 = cleaned_data.get("password2", "")

        if password1 != password2:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["username"]
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data['email']
        if commit:
    	    user.save()    	
        return user

class ReportAbuseForm(Form):
    abuse_description = CharField(required=True, widget=widgets.Textarea())

class MessageToAdminForm(Form):
    message = CharField(required=True, widget=widgets.Textarea())

class AddAdminForm(Form):
    email = EmailField(required=True)
    type = ChoiceField(choices=(('Normal','Normal'),('Power','Power')))
