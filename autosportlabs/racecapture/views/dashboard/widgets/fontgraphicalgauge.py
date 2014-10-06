import kivy
kivy.require('1.8.0')
from utils import kvFind
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.graphicalgauge import GraphicalGauge
class FontGraphicalGauge(GraphicalGauge):
    
    def __init__(self, **kwargs):
        super(FontGraphicalGauge, self).__init__(**kwargs)

    def on_value(self, instance, value):
        max = self.max
        railedValue = value
        if not railedValue == None and not max == None: 
            view = self.graphView
            if railedValue > max:
                railedValue = max
            
            view.text = '' if railedValue == 0 else unichr(ord(u'\uE600') + int(((railedValue * 100) / max)) - 1)
            
            if self.alert and value >= self.alert:
                view.color = self.alert_color
            elif self.warning and value >=self.warning:
                view.color = self.warning_color
            else:
                view.color = self.normal_color
                
            return super(FontGraphicalGauge, self).on_value(instance, value)

