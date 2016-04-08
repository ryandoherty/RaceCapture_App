import kivy
kivy.require('1.9.1')
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.app import Builder
from collections import OrderedDict  
from kivy.metrics import dp
from kivy.graphics import Color
from autosportlabs.racecapture.views.dashboard.widgets.fontgraphicalgauge import FontGraphicalGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/tachometer.kv')

class Tachometer(FontGraphicalGauge):
    def __init__(self, **kwargs):
        super(Tachometer, self).__init__(**kwargs)
        self.initWidgets()
            
    def initWidgets(self):
        pass
        
    def on_touch_down(self, touch, *args):
        pass

    def on_touch_move(self, touch, *args):
        pass

    def on_touch_up(self, touch, *args):
        pass
        
        
        
