import kivy
kivy.require('1.9.1')
from fieldlabel import FieldLabel
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
from autosportlabs.racecapture.views.dashboard.widgets.gauge import SingleChannelGauge, Gauge
Builder.load_file('autosportlabs/racecapture/views/dashboard/laptimeview.kv')

class LaptimeView(Screen):

    _databus = None
    _settings = None
     
    def __init__(self, databus, settings, **kwargs):
        super(LaptimeView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self.initScreen()
        
    def on_meta(self, channelMetas):
        gauges = self.findActiveGauges(SingleChannelGauge)
        
        for gauge in gauges:
            channel = gauge.channel
            if channel:
                channelMeta = channelMetas.get(channel)
                if channelMeta:
                    gauge.precision = channelMeta.precision
                    gauge.min = channelMeta.min
                    gauge.max = channelMeta.max

    def findActiveGauges(self, gauge_type):
        return list(kvFindClass(self, gauge_type))
        
    def initScreen(self):
        dataBus = self._databus
        settings = self._settings
        dataBus.addMetaListener(self.on_meta)
        
        gauges = self.findActiveGauges(Gauge)
        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = dataBus
 
