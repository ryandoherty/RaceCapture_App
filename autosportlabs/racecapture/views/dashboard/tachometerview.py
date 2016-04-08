import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import Tachometer
from autosportlabs.racecapture.views.dashboard.widgets.bignumberview import BigNumberView
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
from autosportlabs.racecapture.views.dashboard.widgets.timedelta import TimeDelta
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from utils import kvFind, kvFindClass

Builder.load_file('autosportlabs/racecapture/views/dashboard/tachometerview.kv')

class TachometerView(Screen):

    _databus = None
    _settings = None
    
    def __init__(self, databus, settings, **kwargs):
        super(TachometerView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self.initScreen()        
                
    def on_meta(self, channelMetas):
        pass
 
    def initScreen(self):
        dataBus = self._databus
        settings = self._settings
        dataBus.addMetaListener(self.on_meta)
        
        gauges = list(kvFindClass(self, Gauge))
        
        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = dataBus
        
            
