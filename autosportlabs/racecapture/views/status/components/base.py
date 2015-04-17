import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout

class BaseComponentStatusView(BoxLayout):

    def __init__(self, **kwargs):
        super(BaseComponentStatusView, self).__init__(**kwargs)
        self.ids.name.text = kwargs.get('title')
