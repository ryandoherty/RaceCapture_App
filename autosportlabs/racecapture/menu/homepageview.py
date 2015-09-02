import kivy
kivy.require('1.9.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.app import Builder
from utils import kvFind
from autosportlabs.uix.iconbutton import TileIconButton
from kivy.metrics import dp
import mainfonts

from autosportlabs.widgets.separator import HLineSeparator

Builder.load_file('autosportlabs/racecapture/menu/homepageview.kv')

class FeatureButton(TileIconButton):
    def __init__(self, **kwargs):
        super(FeatureButton, self).__init__(**kwargs)
        self.tile_color =  (1.0, 1.0, 1.0, 1.0)

class DisabledFeatureButton(FeatureButton):
    def __init__(self, **kwargs):
        super(DisabledFeatureButton, self).__init__(**kwargs)
        self.tile_color = (1.0, 1.0, 1.0, 1.0)
    
class HomePageView(Screen):
    def __init__(self, **kwargs):
        super(HomePageView, self).__init__(**kwargs)
        self.register_event_type('on_select_view')
    
    def on_select_view(self, viewKey):
        pass
    
    def show_view(self, viewKey):
        self.dispatch('on_select_view', viewKey)
        