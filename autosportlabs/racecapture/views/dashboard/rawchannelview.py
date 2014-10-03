import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/dashboard/rawchannelview.kv')

class RawChannelView(Screen):

    def __init__(self, **kwargs):
        super(RawChannelView, self).__init__(**kwargs)
        self.initView()

    def initView(self):
        pass
