import kivy
kivy.require('1.8.0')
from fieldlabel import FieldLabel
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
Builder.load_file('autosportlabs/racecapture/views/dashboard/laptimeview.kv')

class LaptimeView(Screen):

    _databus = None
    _settings = None
     
    def __init__(self, **kwargs):
        super(LaptimeView, self).__init__(**kwargs)
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self.initScreen()

    def on_sample(self, sample):
        pass
        
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
        settings = self._settings
        dataBus.addMetaListener(self.on_meta)
        dataBus.addSampleListener(self.on_sample)
        
        gauges = self.findActiveGauges()
        for gauge in gauges:
            gauge.settings = settings
            gauge.dataBus = dataBus
 
