import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
Builder.load_file('autosportlabs/racecapture/views/status/components/base.kv')

class BaseComponentStatusView(BoxLayout):

    status = None

    def __init__(self, title, status = None):
        super(BaseComponentStatusView, self).__init__(**kwargs)
        self.ids.name.text = title
        self.status = status
        self.render()
