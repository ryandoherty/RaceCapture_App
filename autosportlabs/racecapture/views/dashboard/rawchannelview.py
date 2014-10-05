import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from utils import kvFind
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
from kivy.properties import StringProperty

Builder.load_file('autosportlabs/racecapture/views/dashboard/rawchannelview.kv')

NO_DATA_MSG = 'No Data'
DATA_MSG    = ''

class RawGauge(DigitalGauge):
    
    channel = StringProperty(None)
    
    def __init__(self, **kwargs):
        super(RawGauge  , self).__init__(**kwargs)
        
    def on_channel(self, instance, value):
        self.title = str(value)
            
class RawChannelView(Screen):
    _gauges = []
    _grid = None
    
    def __init__(self, **kwargs):
        super(RawChannelView, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.initView(), 1)
    
    @property
    def _gridView(self):
        if self._grid == None:
            self._grid = kvFind(self, 'rcid', 'grid')
        return self._grid
        
    def initView(self):
        self._addGauge('OilPress', 35)        
        self._addGauge('Distance', 0)
        self._addGauge('Speed', 0)
        self._addGauge('EngineTemp', 189)
        self._addGauge('RPM', 935)
        self._addGauge('AccelX',0.03)
        self._addGauge('AccelY',0.05)
        self._addGauge('AccelZ',1.0)
        self._addGauge('Yaw',0.01)
        self._addGauge('Pitch',0.0)
        self._addGauge('Roll',0.0)

        for i in range (1, 100):
            self._addGauge('channel{}'.format(i), i)
        
        
    def _enableNoDataStatus(self, enabled):
        statusView = kvFind(self, 'rcid', 'statusMsg')
        statusView.text = NO_DATA_MSG if enabled else DATA_MSG
        
    def _addGauge(self, channel, value):
        gauge = RawGauge()
        self._gauges.append(gauge)
        self._gridView.add_widget(gauge)
        gauge.value = value
        gauge.channel = channel
        self._enableNoDataStatus(False)