import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/digitalgauge.kv')

class DigitalGauge(BoxLayout, Gauge):
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super(DigitalGauge, self).__init__(**kwargs)
        self.value_size = dp(50)
        self.title_size = dp(25)
        self._valueView     = None
        self._labelView     = None
        self.initWidgets()
            
    def initWidgets(self):
        self.alert = 0
        self.warning = 0
        self.max = 0
                    
    def on_title(self, instance, value):
        x = 1/0
        view = self._labelView
        if not view:
            view = kvFind(self, 'rcid', 'label')
            self._labelView = view
        view.text = str(value)
        self._label = value
        
    def on_value(self, instance, value):
        view = self._valueView
        if not view:
            view = kvFind(self, 'rcid', 'value')
            self._valueView = view

        self._value = value
        view.text = str(value)
        if value < self.warning:
            view.color = self.normal_color
        elif value < self.alert:
            view.color = self.warning_color
        else:
            view.color = self.alert_color        

    @property
    def gaugeSize(self):
        return self._gaugeSize
    
    @gaugeSize.setter
    def gaugeSize(self, value):
        self._gaugeSize = value
        if not self._valueView == None:
            self._valueView.font_size = value

