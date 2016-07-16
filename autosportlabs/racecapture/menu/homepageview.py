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

HOMPAGE_VIEW_KV = """
<DisabledFeatureButton>
    tile_color: (0.3, 0.3, 0.3, 1.0)
    
<FeatureButton>
    title_font: 'resource/fonts/ASL_regular.ttf'
    icon_color: (0.0, 0.0, 0.0, 1.0)
    title_color: (0.2, 0.2, 0.2, 1.0)
    
<HomePageView>:
    BoxLayout:
        orientation: 'horizontal'
        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'center'
            Image:
                size_hint: (0.7, 0.7)
                source: 'resource/images/app_icon_512x512.png'
        BoxLayout:
            orientation: 'vertical'
            padding: [self.height * 0.05, self.height * 0.05]
            spacing: dp(15)
            FeatureButton:
                size_hint_y: 0.5
                icon: '\357\203\244'
                title: 'Race'
                on_press: root.show_view('dash')
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: 0.5
                spacing: dp(15)
                FeatureButton:
                    icon: '\357\202\200'
                    title: 'Analysis'
                    on_press: root.show_view('analysis')
                FeatureButton:
                    icon: '\357\202\205'
                    title: 'Setup'
                    on_press: root.show_view('config')

"""

class HomePageView(Screen):
    Builder.load_string(HOMPAGE_VIEW_KV)

    def __init__(self, **kwargs):
        super(HomePageView, self).__init__(**kwargs)
        self.register_event_type('on_select_view')

    def on_select_view(self, viewKey):
        pass

    def show_view(self, viewKey):
        self.dispatch('on_select_view', viewKey)
