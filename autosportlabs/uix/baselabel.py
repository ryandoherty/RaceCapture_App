import kivy
kivy.require('1.9.1')

from kivy.uix.label import Label


class BaseLabel(Label):
    def __init__(self, **kwargs):
        super(BaseLabel, self).__init__(**kwargs)
        self.font_name = "resource/fonts/ASL_light.ttf"
