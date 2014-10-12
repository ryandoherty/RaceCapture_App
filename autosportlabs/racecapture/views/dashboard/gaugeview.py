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

    def __init__(self, **kwargs):
        super(GaugeView, self).__init__(**kwargs)
        self.initScreen(kwargs.get('dataBus', None))

    def on_sample(self, sample):
        pass
        
    def on_meta(self, channelMetas):
        pass

    def initScreen(self, dataBus):
        dataBus.addMetaListener(self.on_meta)
        dataBus.addSampleListener(self.on_sample)
        
        gauges = list(kvFindClass(self, Gauge))
        
        for gauge in gauges:
            channel = gauge.channel
            print('gauge found ' + str(gauge) + ' ' + channel)
            if channel:
                dataBus.addChannelListener(channel, gauge.setValue)
        
        self.dataBus = dataBus
 