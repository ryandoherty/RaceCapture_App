import kivy
kivy.require('1.8.0')
from utils import kvFind
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

class GraphicalGauge(Gauge):
    _gaugeView = None
    gauge_size = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super(GraphicalGauge, self).__init__(**kwargs)

    @property
    def graphView(self):
        if not self._gaugeView:
            self._gaugeView = kvFind(self, 'rcid', 'gauge')
        return self._gaugeView