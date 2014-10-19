import kivy
kivy.require('1.8.0')
from utils import kvFind
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.graphicalgauge import GraphicalGauge
class FontGraphicalGauge(GraphicalGauge):
    
    def __init__(self, **kwargs):
        super(FontGraphicalGauge, self).__init__(**kwargs)


    def refreshGaugeDisplay(self):
        try:
            value = self.value
            min = self.min
            max = self.max
            railedValue = value
            view = self.graphView
            if railedValue > max:
                railedValue = max
            if railedValue < min:
                railedValue = min
    
            range = max - min
            offset = railedValue - min
            view.text = '' if offset == 0 else unichr(ord(u'\uE600') + int(((offset * 100) / range)) - 1)
            if self.alert and value >= self.alert:
                view.color = self.alert_color
            elif self.warning and value >=self.warning:
                view.color = self.warning_color
            else:
                view.color = self.normal_color
        except Exception as e:
            print('error setting font gauge value ' + str(e))
        
    def on_value(self, instance, value):
        self.refreshGaugeDisplay()
        return super(FontGraphicalGauge, self).on_value(instance, value)


