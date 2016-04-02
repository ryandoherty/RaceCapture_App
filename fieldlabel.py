import kivy
kivy.require('1.9.1')

from kivy.uix.label import Label
from kivy.metrics import sp

class FieldLabel(Label):
    def __init__(self, **kwargs):
        super(FieldLabel, self).__init__(**kwargs)
        self.bind(width=self.width_changed)
        self.spacing = (20,3)
        self.font_name = "resource/fonts/ASL_light.ttf"
        self.font_size = sp(20)
        self.shorten = True
        self.shorten_from = 'right'
        
    def width_changed(self, instance, size):
        self.text_size = (size, None)
