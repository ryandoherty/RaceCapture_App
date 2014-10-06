import kivy
kivy.require('1.8.0')
from fieldlabel import FieldLabel
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from utils import kvFind
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
Builder.load_file('autosportlabs/racecapture/views/dashboard/laptimeview.kv')

class LaptimeView(Screen):

    def __init__(self, **kwargs):
        super(LaptimeView, self).__init__(**kwargs)
        self.initView()

    def initView(self):
        pass
