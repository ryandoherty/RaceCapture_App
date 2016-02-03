import kivy
kivy.require('1.9.1')
from iconbutton import IconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.properties import ListProperty
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter

Builder.load_file('autosportlabs/racecapture/views/color/colorpickerview.kv')

class ColorBlock(ButtonBehavior, Widget):
    color = ListProperty([1.0, 1.0, 1.0, 1.0])
    
    def on_color(self, instance, value):
        self.canvas.ask_update()
        
class ColorPickerView(FloatLayout):
    color = ListProperty([1.0, 1.0, 1.0, 1.0])
    
    def __init__(self, **kwargs):
        super(ColorPickerView, self).__init__(**kwargs)
        self.color = kwargs.get('color')
        self.register_event_type('on_color_selected')
        self.register_event_type('on_color_cancel')
        Clock.schedule_once(self.init_view)

    def init_view(self, dt):
        color = self.color
        selectedColorBlock = self.ids.selectedColor
        colorWheel = self.ids.colorWheel
        selectedColorBlock.color = color
        colorWheel.color = color
        colorWheel._origin = (colorWheel.pos[0] + colorWheel.center[0] , colorWheel.pos[1] + colorWheel.center[1])
        colorWheel.init_wheel(None)
        colorWheel.bind(color=self.on_color)
        
    def on_color(self, instance, value):
        self.color = value
        selectedColorBlock = self.ids.get('selectedColor')
        if selectedColorBlock:
            selectedColorBlock.color = [value[0], value[1], value[2], value[3]]
        
    def on_select(self, *args):
        self.dispatch('on_color_selected', self.ids.colorWheel.color)
    
    def on_cancel(self):
        self.dispatch('on_color_cancel')

    def on_color_selected(self, selectedTrackIds):
        pass
    
    def on_color_cancel(self):
        pass
    