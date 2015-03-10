import kivy
kivy.require('1.8.0')
from iconbutton import IconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.screenmanager import Screen
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter
from autosportlabs.uix.button.featurebutton import FeatureButton
Builder.load_file('autosportlabs/racecapture/views/analysis/addstreamview.kv')

class AddStreamView(BoxLayout):
    channel = None
    settings = None
    def __init__(self, **kwargs):
        super(AddStreamView, self).__init__(**kwargs)
        
        self.settings = kwargs.get('settings')

    def connect_cloud_stream(self):
        pass
    
        screenMgr = kvFind(self, 'rcid', 'screenmgr')
        screenMgr.add_widget(self.manualTrackConfigView)
        self.screenManager = screenMgr
    
    def connect_wireless_stream(self):
        pass
    
    def connect_file_stream(self):
        pass
        
        
class AddStreamSelectView(Screen):
    pass
    