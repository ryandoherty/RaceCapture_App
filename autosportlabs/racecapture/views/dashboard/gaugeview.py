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

    _dataBus = None
    _settings = None
    _gaugesMap = {}
     
    def __init__(self, **kwargs):
        super(GaugeView, self).__init__(**kwargs)
        self._dataBus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self.initScreen()

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
        
    def initScreen(self):
        dataBus = self._dataBus
        settings = self._settings
        dataBus.addMetaListener(self.on_meta)
        dataBus.addSampleListener(self.on_sample)
        
        gauges = list(kvFindClass(self, Gauge))
        for gauge in gauges:
            gauge.settings = settings
            if gauge.channel:
                dataBus.addChannelListener(gauge.channel, lambda value: Clock.schedule_once(lambda dt: gauge.setValue))
 