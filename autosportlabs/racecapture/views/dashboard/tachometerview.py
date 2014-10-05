import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import Tachometer
from autosportlabs.racecapture.views.dashboard.widgets.bignumberview import BigNumberView
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
from autosportlabs.racecapture.views.dashboard.widgets.timedelta import TimeDelta

from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/dashboard/tachometerview.kv')

class TachometerView(Screen):

    def __init__(self, **kwargs):
        super(TachometerView, self).__init__(**kwargs)
        self.initView()
        Clock.schedule_interval(self.incrementTach, 0.05)
        

    def initView(self):
        pass
    

    def incrementTach(self, dt):
        tach = kvFind(self, 'rcid', 'tach')
        tach.value += 10
        
