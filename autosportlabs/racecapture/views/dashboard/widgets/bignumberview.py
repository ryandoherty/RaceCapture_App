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

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/bignumberview.kv')

DEFAULT_NORMAL_COLOR = [1, 1, 1, 1]
DEFAULT_WARNING_COLOR = [1, 0.79, 0 ,1]
DEFAULT_ALERT_COLOR = [1, 0, 0, 1]

class BigNumberView(AnchorLayout):

    title_font = StringProperty('')
    title_font_size = NumericProperty(20)
    tile_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))    
    icon_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    title_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    icon = StringProperty('')
    title = StringProperty('')
 
    def __init__(self, **kwargs):

    def on_button_press(self, *args):
        self.dispatch('on_press')
        
    def on_press(self, *args):
        pass

    def __init__(self, **kwargs):
        
        super(BigNumberView, self).__init__(**kwargs)
        self.register_event_type('on_press')
        
        self._tileView      = None
        self._warning       = 0
        self._alert         = 0
        self._value         = 0
        self._label         = ''
        self._alertColor    = DEFAULT_ALERT_COLOR
        self._warningColor  = DEFAULT_WARNING_COLOR
        self._normalColor   = DEFAULT_NORMAL_COLOR
        self.initWidgets()
            
    def initWidgets(self):
        self.alert = 0
        self.warning = 0
        self.max = 0
                    
    @property
    def warning(self):
        return self._warning
    
    @warning.setter
    def warning(self, value):
        self._warning = value
        
    @property
    def alert(self):
        return self._alert
    
    @alert.setter
    def alert(self, value):
        self._alert = value

    @property
    def max(self):
        return self._max
    
    @max.setter
    def max(self, value):
        self._max = value

    @property
    def label(self):
        return self._label
    
    @label.setter
    def label(self, value):
        view = self._tileView
        if not view:
            view = kvFind(self, 'rcid', 'view')
            self._tileView = view
        view.title = str(value)
        self._label = value
        
        
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        view = self._tileView
        if not view:
            view = kvFind(self, 'rcid', 'view')
            self._tileView = view

        self._value = value
        view.value = str(value)
        if value < self._warning:
            view.color = self._normalColor
        elif value < self._alert:
            view.color = self._warningColor
        else:
            view.color = self._alertColor        

    @property
    def gaugeSize(self):
        return self._gaugeSize
    
    @gaugeSize.setter
    def gaugeSize(self, value):
        self._gaugeSize = value
        if not self._valueView == None:
            self._valueView.font_size = value

