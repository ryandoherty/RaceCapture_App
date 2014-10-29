import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/dashboard/comboview.kv')

class ComboView(Screen):

    def __init__(self, **kwargs):
        super(ComboView, self).__init__(**kwargs)
        self.init_view()

    def init_view(self):
        pass
