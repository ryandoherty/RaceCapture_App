import kivy
kivy.require('1.9.0')
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind, kvquery
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/imugauge.kv')

class ImuGauge(Gauge):
    
    def __init__(self, **kwargs):
        super(ImuGauge, self).__init__(**kwargs)
        self.initWidgets()
            
    def initWidgets(self):
        pass
