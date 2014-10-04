import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import Tachometer
from autosportlabs.racecapture.views.dashboard.widgets.bignumberview import BigNumberView
from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/dashboard/tachometerview.kv')

class TachometerView(Screen):

    def __init__(self, **kwargs):
        super(TachometerView, self).__init__(**kwargs)
        self.initView()


    def initView(self):
        tach = kvFind(self, 'rcid', 'tach')
        tach.value = 5000
