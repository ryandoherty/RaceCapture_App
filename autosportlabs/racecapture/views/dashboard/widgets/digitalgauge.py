import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind, kvquery
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/digitalgauge.kv')

class DigitalGauge(BoxLayout, Gauge):
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    _valueView = None
    _titleView = None
    
    def __init__(self, **kwargs):
        super(DigitalGauge, self).__init__(**kwargs)
        self.value_size     = dp(50)
        self.title_size     = dp(25)
        self.initWidgets()
            
    def initWidgets(self):
        self.alert = 0
        self.warning = 0
        self.max = 0
                    
    @property
    def valueView(self):
        if not self._valueView:
            self._valueView = kvFind(self, 'dgid', 'value')
        return self._valueView

    @property
    def titleView(self):
        if not self._titleView:
            self._titleView = kvFind(self, 'dgid', 'title')
        return self._titleView
                    
    def on_title(self, instance, value):
        view = self.titleView

        view.text = str(value)
        self._label = value
        
    def on_value(self, instance, value):
        view = self.valueView
        
        self.value = value
        view.text = str(value)
        if self.alert and value >= self.alert:
            view.color = self.alert_color
        elif self.warning and value >=self.warning:
            view.color = self.warning_color
        else:
            view.color = self.normal_color

    @property
    def gaugeSize(self):
        return self._gaugeSize
    
    @gaugeSize.setter
    def gaugeSize(self, value):
        self._gaugeSize = value
        if not self._valueView == None:
            self._valueView.font_size = value

