import kivy
kivy.require('1.8.0')
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.app import Builder
from collections import OrderedDict  
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from iconbutton import TileIconButton
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/bignumberview.kv')

DEFAULT_NORMAL_COLOR  = [0.2, 0.2 , 0.2, 1.0]
DEFAULT_WARNING_COLOR = [1.0, 0.79, 0.2 ,1.0]
DEFAULT_ALERT_COLOR   = [1.0, 0   , 0   , 1 ]

class BigNumberView(AnchorLayout):

    _backgroundView  = None
    _titleView = None
    _valueView = None
    
    title_font = StringProperty('')
    title_font_size = NumericProperty(20)
    
    tile_color = ObjectProperty((0.2, 0.2, 0.2, 1.0))    
    value_color = ObjectProperty((1.0, 1.0, 1.0, 1.0))
    title_color = ObjectProperty((1.0, 1.0, 1.0, 1.0))
    
    title = StringProperty('')
    value = NumericProperty(0)
    warning = NumericProperty(0)
    alert = NumericProperty(0)
    max = NumericProperty(0)

    def on_press(self, *args):
        self.dispatch('on_press')
        pass

    def __init__(self, **kwargs):
        
        super(BigNumberView, self).__init__(**kwargs)
        self.register_event_type('on_press')
        
        self._alertColor    = DEFAULT_ALERT_COLOR
        self._warningColor  = DEFAULT_WARNING_COLOR
        self._normalColor   = DEFAULT_NORMAL_COLOR
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
            
    @property
    def titleView(self):
        if not self._titleView:
            self._titleView = kvFind(self, 'rcid', 'title')
        return self._titleView
    
    @property
    def valueView(self):
        if not self._valueView:
            self._valueView = kvFind(self, 'rcid', 'value')
        return self._valueView
    
    def on_title(self, instance, value):
        self.backgroundView.text = value
        
    def on_value(self, instance, value):
        self.valueView.text = '{0:0}'.format(value)
        self._updateView()
        
    def on_tile_color(self, instance, value):
        self.backgroundView.rect_color = value
        
    def on_value_color(self, instance, value):
        self.valueView.color = value
        
    def on_title_color(self, instance, value):
        self.backgroundView.color = value
        
    def _updateView(self):
        value = self.value
        bgView = self.backgroundView
        if value < self.warning:
            bgView.rect_color = self._normalColor
        elif value < self.alert:
            bgView.rect_color = self._warningColor
        else:
            bgView.rect_color = self._alertColor        
