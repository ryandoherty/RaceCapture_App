import kivy
kivy.require('1.8.0')
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.app import Builder
from collections import OrderedDict  
from kivy.metrics import dp
from kivy.graphics import Color
from autosportlabs.racecapture.views.dashboard.widgets.graphicalgauge import GraphicalGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/tachometer.kv')

TACH_RANGES = OrderedDict([(7000, 'resource/fonts/tach_7000.ttf'), (10000, 'resource/fonts/tach_10000.ttf'), (15000, 'resource/fonts/tach_15000.ttf')])

class Tachometer(AnchorLayout, GraphicalGauge):
    def __init__(self, **kwargs):
        super(Tachometer, self).__init__(**kwargs)
        self.initWidgets()
            
    def initWidgets(self):
        pass
        
        
    def configureRangeFont(self, max):
        graphView = self.graphView
        lastRangeFont = None
        lastRange = 0
        for testRange,font in TACH_RANGES.items():
            lastRangeFont = font
            lastRange = testRange
            if max <= testRange:
                graphView.font_name = font
                return testRange
        
        graphView.font_name = lastRangeFont
        return lastRange
            

    def on_max(self, instance, value):
        self.configureRangeFont(value)
        
    def on_value(self, instance, value):
        max = self.max
        if not value == None and not max == None: 
            view = self.graphView
            if value > max:
                value = max
            
            view.text = '' if value == 0 else unichr(ord(u'\uE600') + ((value * 100) / max) - 1)
            
            if self.alert and value >= self.alert:
                view.color = self.alert_color
            elif self.warning and value >=self.warning:
                view.color = self.warning_color
            else:
                view.color = self.normal_color
                
            return super(Tachometer, self).on_value(instance, value)

