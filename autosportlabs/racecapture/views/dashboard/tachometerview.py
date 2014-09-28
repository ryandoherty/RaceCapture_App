import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import Tachometer
from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/dashboard/tachometerview.kv')

class TachometerView(Screen):
    direction = 100

    def __init__(self, **kwargs):
        super(TachometerView, self).__init__(**kwargs)
        Clock.schedule_interval(self.increment, 0.025)


    def increment(self, dt):
        tach = kvFind(self, 'rcid', 'tach')
        v = tach.value
        v += self.direction
        if v >= 10000 or v <= 0:
            self.direction = -self.direction
        tach.value = v
    