import kivy
kivy.require('1.8.0')
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

    dataBus = None
    def __init__(self, **kwargs):
        super(TachometerView, self).__init__(**kwargs)
        self.initScreen(kwargs.get('dataBus', None))        
        

    def on_sample(self, sample):
        pass
        
    def on_meta(self, channelMetas):
        pass
 
    def initScreen(self, dataBus):
        dataBus.addMetaListener(self.on_meta)
        dataBus.addSampleListener(self.on_sample)
        
        gauges = list(kvFindClass(self, Gauge))
        
        print('init screen')
        for gauge in gauges:
            channel = gauge.channel
            if channel:
                dataBus.addChannelListener(channel, gauge.setValue)
        
        self.dataBus = dataBus
        
            
