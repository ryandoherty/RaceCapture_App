import kivy
kivy.require('1.9.1')
from iconbutton import TileIconButton
from kivy.app import Builder

Builder.load_file('autosportlabs/uix/button/featurebutton.kv')

class FeatureButton(TileIconButton):
    def __init__(self, **kwargs):
        super(FeatureButton, self).__init__(**kwargs)
        self.tile_color =  (1.0, 1.0, 1.0, 1.0)

class DisabledFeatureButton(FeatureButton):
    def __init__(self, **kwargs):
        super(DisabledFeatureButton, self).__init__(**kwargs)
        self.tile_color = (1.0, 1.0, 1.0, 1.0)
