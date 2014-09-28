import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from autosportlabs.racecapture.views.dashboard.widgets.tachometerview import TachometerView
from utils import kvFind
Builder.load_file('autosportlabs/racecapture/views/dashboard/dashboardview.kv')

class DashboardView(Screen):
    
    direction = 100
    def __init__(self, **kwargs):
        super(DashboardView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        Clock.schedule_interval(self.increment, 0.025)
            
    def on_tracks_updated(self, trackManager):
        pass


    def increment(self, dt):
        tach = kvFind(self, 'rcid', 'tach')
        v = tach.value
        v += self.direction
        if v >= 10000 or v <= 0:
            self.direction = -self.direction
        tach.value = v
        
        