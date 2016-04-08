import kivy
kivy.require('1.9.1')
from utils import kvFind
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.graphicalgauge import GraphicalGauge
class FontGraphicalGauge(GraphicalGauge):
    
    def __init__(self, **kwargs):
        super(FontGraphicalGauge, self).__init__(**kwargs)

    def on_min(self, instance, value):
        self._refresh_gauge()
        
    def on_max(self, instance, value):
        self._refresh_gauge()
        
    def update_colors(self):
        self.graphView.color = self.select_alert_color()
        return super(FontGraphicalGauge, self).update_colors()
        
    def _refresh_gauge(self):
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
                
        except Exception as e:
            print('error setting font gauge value ' + str(e))
        
    def on_value(self, instance, value):
        self._refresh_gauge()
        return super(FontGraphicalGauge, self).on_value(instance, value)


