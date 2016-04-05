import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.app import Builder
from kivy.metrics import dp
import mainfonts
from utils import kvFind
from autosportlabs.uix.button.featurebutton import FeatureButton

from autosportlabs.widgets.separator import HLineSeparator

Builder.load_file('autosportlabs/racecapture/menu/homepageview.kv')
    
class HomePageView(Screen):
    def __init__(self, **kwargs):
        super(HomePageView, self).__init__(**kwargs)
        self.register_event_type('on_select_view')
    
    def on_select_view(self, viewKey):
        pass
    
    def show_view(self, viewKey):
        self.dispatch('on_select_view', viewKey)
        