import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from collections import OrderedDict  
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/digitalgauge.kv')

DEFAULT_NORMAL_COLOR = [1, 1, 1, 1]
DEFAULT_WARNING_COLOR = [1, 0.79, 0 ,1]
DEFAULT_ALERT_COLOR = [1, 0, 0, 1]

class DigitalGauge(BoxLayout):
    def __init__(self, **kwargs):
        super(DigitalGauge, self).__init__(**kwargs)
        self._valueView     = None
        self._labelView     = None
        self._warning       = 0
        self._alert         = 0
        self._value         = 0
        self._label         = ''
        self._alertColor    = DEFAULT_ALERT_COLOR
        self._warningColor  = DEFAULT_WARNING_COLOR
        self._normalColor   = DEFAULT_NORMAL_COLOR
        self.initWidgets()
            
    def initWidgets(self):
        self.alert = 0
        self.warning = 0
        self.max = 0
                    
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
        self._max = value

    @property
    def label(self):
        return self._label
    
    @label.setter
    def label(self, value):
        view = self._labelView
        if not view:
            view = kvFind(self, 'rcid', 'label')
            self._labelView = view
        view.text = str(value)
        self._label = value
        
        
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        view = self._valueView
        if not view:
            view = kvFind(self, 'rcid', 'value')
            self._valueView = view

        self._value = value
        view.text = str(value)
        if value < self._warning:
            view.color = self._normalColor
        elif value < self._alert:
            view.color = self._warningColor
        else:
            view.color = self._alertColor        

    @property
    def gaugeSize(self):
        return self._gaugeSize
    
    @gaugeSize.setter
    def gaugeSize(self, value):
        self._gaugeSize = value
        if not self._valueView == None:
            self._valueView.font_size = value

