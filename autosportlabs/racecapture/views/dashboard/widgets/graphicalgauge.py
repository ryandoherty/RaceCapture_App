import kivy
kivy.require('1.8.0')
from utils import kvFind
from kivy.core.window import Window
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

class GraphicalGauge(Gauge):
    _gaugeView = None
    gauge_size = NumericProperty(0)
    gauge_pct = NumericProperty(0)
    
    def _update_gauge_height(self, pct):
        self.gauge_size = Window.height * self.gauge_pct
        
    def on_gauge_pct(self, instance, value):
        self._update_gauge_height(value)
    
    def __init__(self, **kwargs):
        super(GraphicalGauge, self).__init__(**kwargs)

    def on_pos(self, instance, value):
        self._update_gauge_height(self.gauge_pct)
        
    @property
    def graphView(self):
        if not self._gaugeView:
            self._gaugeView = kvFind(self, 'rcid', 'gauge')
        return self._gaugeView
    
    