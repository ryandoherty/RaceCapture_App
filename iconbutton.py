import kivy
kivy.require('1.9.1')
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.graphics import Color
from kivy.metrics import sp, dp
from kivy.properties import NumericProperty, ListProperty, StringProperty, ObjectProperty
from fieldlabel import FieldLabel
from math import sin, cos, pi
from autosportlabs.racecapture.theme.color import ColorScheme 

Builder.load_file('iconbutton.kv')

class IconButton(Button):
    def __init__(self, **kwargs):
        super(IconButton, self).__init__(**kwargs)

class RoundedRect(BoxLayout):
    rect_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))
    line_width = NumericProperty(dp(10))
    radius = NumericProperty(10)
        
class TileIconButton(ButtonBehavior, AnchorLayout):
    title_font = StringProperty('')
    title_font_size = NumericProperty(20)
    tile_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))    
    icon_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    title_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    icon = StringProperty('')
    title = StringProperty('')
 
    def __init__(self, **kwargs):
        super(TileIconButton, self).__init__(**kwargs)
    
class LabelIconButton(ButtonBehavior, AnchorLayout):
    title_font = StringProperty('resource/fonts/ASL_regular.ttf')
    title_font_size = NumericProperty(sp(20))
    tile_color = ObjectProperty(ColorScheme.get_accent())    
    icon_color = ObjectProperty((0.0, 0.0, 0.0, 1.0))
    title_color = ObjectProperty((0.0, 0.0, 0.0, 1.9))
    icon = StringProperty('')
    icon_size = NumericProperty(sp(25))
    title = StringProperty('')
    
    def __init__(self, **kwargs):
        super(LabelIconButton, self).__init__(**kwargs)
        