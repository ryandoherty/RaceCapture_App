import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from collections import OrderedDict  
from kivy.metrics import dp
from kivy.graphics import Color

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/tachometer.kv')

TACH_RANGES = OrderedDict([(7000, 'resource/fonts/tach_7000.ttf'), (10000, 'resource/fonts/tach_10000.ttf'), (15000, 'resource/fonts/tach_15000.ttf')])
DEFAULT_RANGE = 10000
START_CHAR = u'\uE600'
DEFAULT_NORMAL_COLOR = [1, 1, 1, 1]
DEFAULT_WARNING_COLOR = [1, 0.79, 0 ,1]
DEFAULT_ALERT_COLOR = [1, 0, 0, 1]

class Tachometer(BoxLayout):
    def __init__(self, **kwargs):
        super(Tachometer, self).__init__(**kwargs)
        self._range         = DEFAULT_RANGE
        self._warning       = 0
        self._alert         = 0
        self._max           = 0
        self._value         = 0
        self._graphSize     = 0
        self._graph         = None
        self._alertColor    = DEFAULT_ALERT_COLOR
        self._warningColor  = DEFAULT_WARNING_COLOR
        self._normalColor   = DEFAULT_NORMAL_COLOR
        self.initWidgets()
            
    def initWidgets(self):
        graph = Label()
        self.add_widget(graph)
        self._graph = graph
        self._range = DEFAULT_RANGE
        self.value = 0
        self.alert = DEFAULT_RANGE * 0.8
        self.warning = DEFAULT_RANGE * 0.7
        self.max = DEFAULT_RANGE
        self.value = 0
        
        
    def configureRangeFont(self, range):
        lastRangeFont = None
        lastRange = 0
        for testRange,font in TACH_RANGES.items():
            lastRangeFont = font
            lastRange = testRange
            if range <= testRange:
                self._graph.font_name = font
                return testRange
        
        self._graph.font_name = lastRangeFont
        return lastRange
            
    @property
    def warning(self):
        return self._warning
    
    @warning.setter
    def warning(self, value):
        self._warning = value
        
    @property
    def alert(self):
        return self._alert
    
    @alert.setter
    def alert(self, value):
        self._alert = value

    @property
    def max(self):
        return self._max
    
    @max.setter
    def max(self, value):
        self._range = self.configureRangeFont(value)
        self._max = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        graph = self._graph
        self._value = value
        if value > self._range:
            value = self._range
        graph.text = '' if value == 0 else unichr(ord(u'\uE600') + (value / 100) - 1)
        if value < self._warning:
            graph.color = self._normalColor
        elif value < self._alert:
            graph.color = self._warningColor
        else:
            graph.color = self._alertColor        

    @property
    def graphSize(self):
        return self._graphSize
    
    @graphSize.setter
    def graphSize(self, value):
        self._graphSize = value
        if not self._graph == None:
            self._graph.font_size = value

