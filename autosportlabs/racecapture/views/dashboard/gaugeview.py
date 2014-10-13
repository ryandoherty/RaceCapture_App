import kivy
kivy.require('1.8.0')
from fieldlabel import FieldLabel
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.roundgauge import RoundGauge
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/gaugeview.kv')

class GaugeView(Screen):

    _gaugesMap = {}
     
    def __init__(self, **kwargs):
        super(GaugeView, self).__init__(**kwargs)
        self.initScreen(kwargs.get('dataBus', None))

    def findActiveGauges(self):
        gauges = list(kvFindClass(self, Gauge))
        for gauge in gauges:
            self._gaugesMap[gauge.channel] = gauge
            
        return self._gaugesMap

    def on_sample(self, sample):
        pass
        
    def on_meta(self, channelMetas):
        gauges = self.findActiveGauges()
        
        for channelMeta in channelMetas:
            name = channelMeta.name
            gauge = gauges.get(name)
            if gauge:
                gauge.precision = channelMeta.precision
                gauge.min = channelMeta.min
                gauge.max = channelMeta.max
        
    def initScreen(self, dataBus):
        dataBus.addMetaListener(self.on_meta)
        dataBus.addSampleListener(self.on_sample)
        
        gauges = self.findActiveGauges()
        
        for channel, gauge in gauges.iteritems():
            dataBus.addChannelListener(channel, lambda value: Clock.schedule_once(lambda dt: gauge.setValue))
        
        self.dataBus = dataBus
 