import kivy
kivy.require('1.8.0')
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.app import Builder
from collections import OrderedDict  
from kivy.metrics import dp
from kivy.graphics import Color
from autosportlabs.racecapture.views.dashboard.widgets.fontgraphicalgauge import FontGraphicalGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/tachometer.kv')

TACH_RANGES = OrderedDict([(7000, 'resource/fonts/tach_7000.ttf'), (10000, 'resource/fonts/tach_10000.ttf'), (15000, 'resource/fonts/tach_15000.ttf')])

class Tachometer(FontGraphicalGauge):
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
        
