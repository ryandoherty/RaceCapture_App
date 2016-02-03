import kivy
kivy.require('1.9.1')
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from utils import *
from sampleratespinner import SampleRateSpinner

from kivy.app import Builder
Builder.load_file('samplerateview.kv')            


class SampleRateSelectorView(BoxLayout):
    def __init__(self, **kwargs):
        super(SampleRateSelectorView, self).__init__(**kwargs)
        self.register_event_type('on_sample_rate')

    def on_sample_rate(self, value):
        pass
    
    def setValue(self, value, max_rate = None):
        if max_rate:
            self.set_max_rate(max_rate)
        kvFind(self, 'rcid', 'sampleRate').setFromValue(value)

    def onSelect(self, instance, value):
        selectedValue = instance.getSelectedValue()
        self.dispatch('on_sample_rate', int(selectedValue) if selectedValue is not None else 0)
        
    def set_max_rate(self, max):
        kvFind(self, 'rcid', 'sampleRate').set_max_rate(max)
