import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind, kvquery
from kivy.properties import NumericProperty, ObjectProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import CustomizableGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/digitalgauge.kv')

DEFAULT_BACKGROUND_COLOR = [0, 0, 0, 0]

class DigitalGauge(CustomizableGauge):

    alert_background_color = ObjectProperty(DEFAULT_BACKGROUND_COLOR)        
    
    def __init__(self, **kwargs):
        super(DigitalGauge, self).__init__(**kwargs)
        self.normal_color = DEFAULT_BACKGROUND_COLOR

    def update_title(self, channel, channel_meta):
        try:
            self.title = channel if channel else ''
        except Exception as e:
            print('Failed to update digital gauge title ' + str(e))

    def update_colors(self):
        self.alert_background_color = self.select_alert_color()
