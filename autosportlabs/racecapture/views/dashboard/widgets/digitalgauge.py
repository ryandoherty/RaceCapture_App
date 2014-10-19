import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind, kvquery
from kivy.properties import NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/digitalgauge.kv')

class DigitalGauge(Gauge):
    
    def __init__(self, **kwargs):
        super(DigitalGauge, self).__init__(**kwargs)
        self.initWidgets()
            
    def initWidgets(self):
        pass

    def updateTitle(self):
        try:
            self.title = self.channel if self.channel else ''
        except Exception as e:
            print('Failed to update digital gauge title ' + str(e))
