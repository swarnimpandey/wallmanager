from datetime import datetime, time
from django.core import mail
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files import File
from django.db.models.signals import pre_save, post_save, post_delete

from appman.models import *
from appman.signals import get_app_dir
from appman.utils.fileutils import relative
from appman.tests.uncompress import UncompressTest

class ApplicationManagementTest(TestCase):
    def __init__(self, *args, **kwargs):
        super(ApplicationManagementTest, self).__init__(*args, **kwargs)
        
        # Turn off signals
        pre_save.receivers = []
        post_save.receivers = []
        post_delete.receivers = []
    
    def setUp(self):
        #Creates usernames for Zacarias and Prof. Plum
        self.zacarias = User.objects.create_user(username="zacarias_stu", email="zacarias@student.dei.uc.pt", password="zacarias")
        self.plum = User.objects.create_user(username="plum_ede", email="plum@dei.uc.pt", password="plum")
        self.plum.is_staff = True
        self.plum.is_superuser = True
        self.plum.save()
        		
        self.educational = Category.objects.create(name="Educational")
        self.games = Category.objects.create(name="Games")
        
        self.gps = Application.objects.create(name="Gps Application", owner=self.zacarias, category=self.educational)
        
    def do_login(self):
        """ Fakes login as standard user. """
        login = self.client.login(username='zacarias_stu', password='zacarias')
        self.assertEqual(login, True)
        return login

    def do_admin_login(self):
        """ Fakes login as administrator. """
        login = self.client.login(username='plum_ede', password='plum')
        self.assertEqual(login, True)
        return login
   
    def test_models_representation(self):
        """ Tests if categories are being well represented as strings. """
        self.assertEqual( unicode(self.educational), u"Educational" )
        self.assertEqual( unicode(self.gps), u"Gps Application" )
    
    def test_application_value(self):
        """ Tests application ratings. """
        self.gps.likes = 5
        self.gps.dislikes = 3
        self.gps.save()
        self.assertEqual( self.gps.value(), 0.625)
        self.assertEqual( self.gps.stars(), 3)
    
    def test_uniqueness_control(self):
        """ Tests uniqueness of the Projector Control object. """
        c1 = ProjectorControl.objects.create(inactivity_time=1, startup_time=time(1), shutdown_time=time(2))
        c2 = ProjectorControl.objects.create(inactivity_time=1, startup_time=time(1), shutdown_time=time(3))
        self.assertEqual( ProjectorControl.objects.count(), 1)
        
    def test_application_log_representation(self):
        """ Tests if logs are well represented. """
        self.log = ApplicationLog.objects.create(application=self.gps, error_description="Error importing library X.")
        self.log.datetime = datetime(2010,1,1,15,0,1)
        self.log.save()
        self.assertEqual( unicode(self.log),  u"Gps Application log at 2010-01-01 15:00:01")

    def test_list_app(self):
        """ Tests application listing. """
        login = self.do_login()
        response = self.client.get('/applications/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gps Application</a></td>")
        self.assertContains(response, "<tr>", 2) # 1 app, plus header
        
    def test_detail_app(self):
        """ Tests the application page. """
        response = self.client.get('/applications/%s/' % self.gps.id )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gps Application")
        self.assertContains(response, "Edit Application",0)
        
        login = self.do_login()
        response = self.client.get('/applications/%s/' % self.gps.id )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Application",1)

    def test_requires_login_to_add_app(self):
        """ Tests the login requirement for the add application page. """
        response = self.client.get('/applications/add/')
        self.assertEqual(response.status_code, 302) # redirect to login
        self.assertRedirects(response, '/accounts/login/?next=/applications/add/')
    
    def test_add_app(self):
        """ Tests the application insersion. """
        login = self.do_login()
        response = self.client.get('/applications/add/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add Application")
        self.assertContains(response, "<form", 1)

        zf = open(relative('../../tests/python_test_app.zip'),'rb')
        pf = open(relative('../../tests/wmlogo.png'),'rb')
        post_data = {
            'name': 'Example App',
            'zipfile': zf,
            'icon': pf,
            'category': self.educational.id, 
            'description': "Example app"
        }
        response = self.client.post('/applications/add/', post_data)
        zf.close()
        pf.close()

        self.assertRedirects(response, '/applications/%s/' % Application.objects.get(name='Example App').id)
        response = self.client.get('/applications/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example App</a></td>")
            
    def test_requires_login_to_edit_app(self):
        """ Tests login requirements for edit application. """
        response = self.client.get('/applications/%s/edit/' % self.gps.id)
        self.assertEqual(response.status_code, 302) # redirect to login
        self.assertRedirects(response, '/accounts/login/?next=/applications/%s/edit/' % self.gps.id)

    def test_edit_app(self):
        """ Tests edit application page. """
        login = self.do_login()
        response = self.client.get('/applications/%s/edit/' % self.gps.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Application")
        
        zf = open(relative('../../tests/python_test_app.zip'),'rb')
        pf = open(relative('../../tests/wmlogo.png'),'rb')
        post_data = {
            'name': 'Example App 2',
            'zipfile': zf,
            'icon': pf,
            'category': self.educational.id, 
            'description': "Example app"
        }
        
        response = self.client.post('/applications/%s/edit/' % self.gps.id, post_data)
        zf.close()
        pf.close()
        
        self.assertRedirects(response, '/applications/%s/' % self.gps.id)
        response = self.client.get('/applications/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example App 2</a></td>")

    def test_delete_app(self):
        """ Tests delete application page. """
        c = Application.objects.count()
        login = self.do_login()
        response = self.client.get('/applications/%s/delete/' % self.gps.id)
        self.assertRedirects(response, '/applications/')
        self.assertEqual(c-1, Application.objects.count())

    def test_requires_staff_to_remove_app(self):
        """ Tests administration permition to remove application. """
        c = Application.objects.count()
        login = self.do_login()
        response = self.client.get('/applications/%s/remove/' % self.gps.id)
        self.assertRedirects(response, '/accounts/login/?next=/applications/%s/remove/'% self.gps.id)
        self.assertEqual(c, Application.objects.count())
        
    def test_remove_app(self):
        """ Tests remove application by admin. """
        # Clean email inbox
        mail.outbox = []
        
        c = Application.objects.count()
        login = self.do_admin_login()
        response = self.client.get('/applications/%s/remove/' % self.gps.id)
        self.assertRedirects(response, '/applications/')
        self.assertEqual(c-1, Application.objects.count())
        
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue("Application removed from the wall" in mail.outbox[0].subject)
    
    
    def test_authorized_list_cat(self):
        """ Test category list page. """
        login = self.do_admin_login()
        response = self.client.get('/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Games</td>")
        self.assertContains(response, "<tr>", Category.objects.count()+1) # 2 cat, plus header
    
    def test_authorized_add_category(self):
        """ Test category insersion page. """
        c = Category.objects.count()
        login = self.do_admin_login()
        post_data = {
            'name': 'Action'
        }
        response = self.client.post('/categories/add/', post_data)
        self.assertRedirects(response, '/categories/')
        self.assertEqual(c+1, Category.objects.count())

    def test_unauthorized_add_category(self):
        """ Tests permition to add category. """
        c = Category.objects.count()
        login = self.do_login()
        post_data = {
            'name': 'Action'
        }
        response = self.client.post('/categories/add/', post_data)
        self.assertRedirects(response, '/accounts/login/?next=/categories/add/')
        self.assertEqual(c, Category.objects.count())

    def test_edit_cat(self):
        """ Test category edition. """
        login = self.do_admin_login()
        #change educational to Work
        post_data = {
            'name': 'Work'
        }
        response = self.client.post('/categories/%s/edit/'%self.gps.category.id, post_data)
        #see if it changed
        response = self.client.get('/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Work</td>")
        self.assertContains(response, "<tr>", Category.objects.count()+1) # 2 cat, plus header
        #confirm that the application category changed to work
        response = self.client.get('/applications/%s/' % self.gps.id )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Work")

    def test_remove_unused_cat(self):
        """ Test removal of empty category. """
        login = self.do_admin_login()
        c = Category.objects.count()
        response = self.client.post('/categories/%s/remove/'%self.games.id)
        self.assertRedirects(response, '/categories/')
        self.assertEqual(c-1, Category.objects.count())

    def test_remove_used_cat(self):
        """ Test removal of non-empty category. """
        login = self.do_admin_login()
        c = Category.objects.count()
        response = self.client.post('/categories/%s/remove/'%self.gps.category.id)
        self.assertRedirects(response, '/categories/')
        #confirm that category unknow appeared
        response = self.client.get('/categories/')
        self.assertContains(response, DEFAULT_CATEGORY)        

        #confirm that the application category changed
        response = self.client.get('/applications/%s/'%self.gps.id)
        self.assertContains(response, DEFAULT_CATEGORY)                

    def test_default_category(self):
        """ Test existence of default category. """
        self.assertEqual(Category.objects.filter(name=DEFAULT_CATEGORY).count(), 1)
    
    def tearDown(self):
        pass
        