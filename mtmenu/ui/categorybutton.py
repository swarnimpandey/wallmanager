from pymt import *


class CategoryButton( MTKineticItem ):

    def __init__( self, cat, **kwargs ):
        self.category = cat
        if cat:
            kwargs.setdefault('label', cat.name)
        else:
            kwargs.setdefault('label', 'All')
        kwargs.setdefault('size', (120,40))
        kwargs.setdefault('font_size', 12)
        kwargs.setdefault('deletable', False)
        super(CategoryButton, self).__init__(**kwargs)



    def on_press( self, touch ):
        from ui import apps_grid, category_grid
        apps_grid.refresh( self.category ) #update applications
        category_grid.refresh() #update categories
        

    def on_release( self, touch ):
        return

