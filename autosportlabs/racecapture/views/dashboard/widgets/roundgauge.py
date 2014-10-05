import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.graphicalgauge import GraphicalGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/roundgauge.kv')

class RoundGauge(AnchorLayout, GraphicalGauge):
    
    def __init__(self, **kwargs):
        super(RoundGauge, self).__init__(**kwargs)
        self.initWidgets()
            
    def initWidgets(self):
        pass
                                        
    def on_title(self, instance, value):
        view = self.titleView

        view.text = str(value)
        self._label = value
        
    def on_value(self, instance, value):
        max = self.max
        view = self.graphView
        if value > max:
            value = max
        
        view.text = '' if value == 0 else unichr(ord(u'\uE600') + ((value * 100) / max) - 1)
        
        if self.alert and value >= self.alert:
            view.color = self.alert_color
        elif self.warning and value >=self.warning:
            view.color = self.warning_color
        else:
            view.color = self.normal_color
            
        return super(RoundGauge, self).on_value(instance, value)
