import kivy
kivy.require('1.9.1')
from fieldlabel import FieldLabel
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from utils import kvFind, kvFindClass
from kivy.metrics import dp
from autosportlabs.racecapture.views.dashboard.widgets.roundgauge import RoundGauge
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/gaugeview.kv')

class GaugeView(Screen):

    _databus = None
    _settings = None
     
    def __init__(self, databus, settings, **kwargs):
        super(GaugeView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self.initScreen()

    def pct(self, p):
        return pct_h(p)
            
    def on_meta(self, channelMetas):
        gauges = self.findActiveGauges()
        
        for gauge in gauges:
            channel = gauge.channel
            if channel:
                channelMeta = channelMetas.get(channel)
                if channelMeta:
                    gauge.precision = channelMeta.precision
                    gauge.min = channelMeta.min
                    gauge.max = channelMeta.max

    def findActiveGauges(self):
        return list(kvFindClass(self, Gauge))

    def initScreen(self):
        dataBus = self._databus
        dataBus.addMetaListener(self.on_meta)
    
        gauges = self.findActiveGauges()
        for gauge in gauges:
            gauge.settings = self._settings
            gauge.data_bus = dataBus
            channel = self._settings.userPrefs.get_gauge_config(gauge.rcid)
            if channel:
                gauge.channel = channel
