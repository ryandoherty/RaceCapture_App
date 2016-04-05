import kivy
kivy.require('1.9.1')
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.app import Builder
from collections import OrderedDict  
from kivy.metrics import dp, sp
from kivy.graphics import Color
from utils import kvFind
from iconbutton import TileIconButton
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import CustomizableGauge
Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/bignumberview.kv')

DEFAULT_NORMAL_COLOR  = [0.2, 0.2 , 0.2, 1.0]
DEFAULT_VALUE_FONT_SIZE = sp(180)
DEFAULT_TITLE_FONT_SIZE = sp(25)

class BigNumberView(CustomizableGauge):

    _backgroundView  = None
    title_font_size = NumericProperty(DEFAULT_TITLE_FONT_SIZE)
    value_font_size = NumericProperty(DEFAULT_VALUE_FONT_SIZE)
    
    tile_color = ObjectProperty((0.2, 0.2, 0.2, 1.0))    
    value_color = ObjectProperty((1.0, 1.0, 1.0, 1.0))
    title_color = ObjectProperty((1.0, 1.0, 1.0, 1.0))
                
    def __init__(self, **kwargs):
        
        super(BigNumberView, self).__init__(**kwargs)
        self.normal_color   = DEFAULT_NORMAL_COLOR
        self.initWidgets()
            
    def initWidgets(self):
        self.alert = 0
        self.warning = 0
        self.max = 0
        
    @property
    def backgroundView(self):
        if not self._backgroundView:
            self._backgroundView = kvFind(self, 'rcid', 'bg')
        return self._backgroundView
                
    def on_title(self, instance, value):
        self.backgroundView.text = str(value) if value else ''
                
    def on_tile_color(self, instance, value):
        self.backgroundView.rect_color = value
        
    def on_value_color(self, instance, value):
        self.valueView.color = value
                
    def update_colors(self):
        self.backgroundView.rect_color = self.select_alert_color()

    def on_channel(self, instance, value):
        self.valueView.font_size = DEFAULT_VALUE_FONT_SIZE
        return super(BigNumberView, self).on_channel(instance, value)
   
    def update_title(self, channel, channel_meta):
        try:
            self.title = channel if channel else ''
        except Exception as e:
            print('Failed to update digital gauge title ' + str(e))

    def change_font_size(self):
        valueView = self.valueView
        try:
            if valueView.texture_size[0] > valueView.width or valueView.texture_size[1] > valueView.height:
                valueView.font_size -= 1
        except Exception as e:
            print('Failed to change font size ' + str(e))
                
    