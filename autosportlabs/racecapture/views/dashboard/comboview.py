import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from kivy.uix.screenmanager import Screen, ScreenManager
from autosportlabs.racecapture.views.dashboard.widgets.imugauge import ImuGauge
from kivy.clock import Clock
from utils import kvFindClass

Builder.load_file('autosportlabs/racecapture/views/dashboard/comboview.kv')

class ComboView(Screen):

    def __init__(self, databus, settings, **kwargs):
        super(ComboView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = databus
        self._settings = settings
        self.init_view()

    def init_view(self):
        data_bus = self._databus
        settings = self._settings
        
        gauges = list(kvFindClass(self, Gauge))
        
        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = data_bus        
            
    def on_tracks_updated(self, trackmanager):
        pass
