import kivy
kivy.require('1.9.0')
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.graphics import Color
from kivy.properties import NumericProperty, ListProperty, StringProperty, ObjectProperty
from fieldlabel import FieldLabel
from math import sin, cos, pi

Builder.load_file('iconbutton.kv')

class IconButton(Button):
    def __init__(self, **kwargs):
        super(IconButton, self).__init__(**kwargs)

class RoundedRect(BoxLayout):
    rect_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))
    line_width = NumericProperty(10)
    points = ObjectProperty((0,0,0,0,0))
    radius = NumericProperty(10)
        
class TileIconButton(AnchorLayout):
    title_font = StringProperty('')
    title_font_size = NumericProperty(20)
    tile_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))    
    icon_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    title_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    icon = StringProperty('')
    title = StringProperty('')
 
    def __init__(self, **kwargs):
        super(TileIconButton, self).__init__(**kwargs)
        self.register_event_type('on_press')

    def on_button_press(self, *args):
        self.dispatch('on_press')
        
    def on_press(self, *args):
        pass
    
class LabelIconButton(ButtonBehavior, AnchorLayout):
    title_font = StringProperty('resource/fonts/ASL_regular.ttf')
    title_font_size = NumericProperty(20)
    tile_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))    
    icon_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    title_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    icon = StringProperty('')
    title = StringProperty('')
    
    def __init__(self, **kwargs):
        super(LabelIconButton, self).__init__(**kwargs)
        
        
    def pressed(self, *args):
        self.dispatch('on_press')
