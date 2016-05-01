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
from kivy.clock import Clock

Builder.load_file('iconbutton.kv')

class IconButton(Button):
    FADED_ALPHA = 0.1
    BRIGHT_ALPHA = 1.0
    FADE_STEP = 0.05
    FADE_INTERVAL = 0.025
    FADE_DELAY = 5.0
    
    def __init__(self, **kwargs):
        super(IconButton, self).__init__(**kwargs)
        self._current_alpha = None
        self.brighten_mode = True
        self._schedule_fade = Clock.create_trigger(self._fade_back, self.FADE_DELAY)
        self._schedule_step = Clock.create_trigger(self._fade_step)
    
    def _fade_step(self, *args):
        if self.brighten_mode == True:
            if self._current_alpha < self.BRIGHT_ALPHA:
                self._current_alpha += self.FADE_STEP
                self._schedule_step()
            
        if self.brighten_mode == False:
            if self._current_alpha > self.FADED_ALPHA:
                self._current_alpha -= self.FADE_STEP
                self._schedule_step()

        color = self.color
        self.color = [color[0], color[1], color[3], self._current_alpha]
             
    def _fade_back(self, *args):
        self.fade()
    
    def _start_transition(self):
        if self._current_alpha is None:
            self._current_alpha = self.color[3]
        self._schedule_step()
        
    def fade(self):
        '''
        Fade this button away to a shadow with low alpha value
        '''
        self.brighten_mode = False
        self._start_transition()

    def brighten(self):
        '''
        Brighten this button
        '''        
        self.brighten_mode = True
        self._start_transition()
        self._schedule_fade()

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
        