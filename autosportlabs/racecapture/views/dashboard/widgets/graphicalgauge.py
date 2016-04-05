import kivy
kivy.require('1.9.1')
from utils import kvFind
from kivy.core.window import Window
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import CustomizableGauge

class GraphicalGauge(CustomizableGauge):
    _gaugeView = None
    gauge_size = NumericProperty(0)
    
    def _update_gauge_size(self, size):
        self.gauge_size = size
            
    def __init__(self, **kwargs):
        super(GraphicalGauge, self).__init__(**kwargs)

    def on_size(self, instance, value):
        width = value[0]
        height = value[1]
        size = width if width < height else height
        self._update_gauge_size(size)
        
    @property
    def graphView(self):
        if not self._gaugeView:
            self._gaugeView = kvFind(self, 'rcid', 'gauge')
        return self._gaugeView
    
    