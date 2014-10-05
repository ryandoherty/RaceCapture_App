import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from utils import kvFind
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/rawchannelview.kv')

class RawGauge(DigitalGauge):
    channel = None
    
    def __init__(self, **kwargs):
        super(RawGauge  , self).__init__(**kwargs)
        self.channel = kwargs.get('channel', self.channel)
        self.label = self.channel
            
class RawChannelView(Screen):
    _gauges = []
    _grid = None
    
    def __init__(self, **kwargs):
        super(RawChannelView, self).__init__(**kwargs)
       #Clock.schedule_once(lambda dt: self.initView())
    
    @property
    def _gridView(self):
        if self._grid == None:
            self._grid = kvFind(self, 'rcid', 'grid')
        return self._grid
        
    def initView(self):
        for i in range (1, 30):
            self._addGauge('channel {}'.format(i))

    def _addGauge(self, channel):
        gauge = RawGauge(channel=channel)
        self._gauges.append(gauge)
        self._gridView.add_widget(gauge)
        