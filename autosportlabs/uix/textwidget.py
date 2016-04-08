import kivy
kivy.require('1.9.1')

from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.metrics import sp
from kivy.lang import Builder

class TextWidget(Label):
    def __init__(self, **kwargs):
        super(TextWidget, self).__init__(**kwargs)
        self.bind(width=self.width_changed)
        self.spacing = (20,3)
        self.font_name = "resource/fonts/ASL_light.ttf"
        self.font_size = sp(20)

    def width_changed(self, instance, size):
        self.text_size = (size, None)


Builder.load_string('''
<FieldInput>:
    font_size: self.height * .5
    multiline: False
    font_name: "resource/fonts/ASL_light.ttf"
''')

class FieldInput(TextInput):
    def __init__(self, **kwargs):
        super(FieldInput, self).__init__(**kwargs)
    