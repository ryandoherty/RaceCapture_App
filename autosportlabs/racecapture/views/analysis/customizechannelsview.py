import os
from threading import Thread
import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.screenmanager import Screen
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter
from autosportlabs.uix.button.featurebutton import FeatureButton
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from iconbutton import IconButton

Builder.load_file('autosportlabs/racecapture/views/analysis/customizechannelsview.kv')

class CustomizeChannelsView(BoxLayout):
    def __init__(self, **kwargs):
        super(CustomizeChannelsView, self).__init__(**kwargs)
        settings = kwargs.get('settings')
        datastore = kwargs.get('datastore')
        
        current_channels_view = self.ids.currentChannelsView
        current_channels_view.bind(on_channel_removed=self.channel_removed)
        current_channels_view.settings = settings
        current_channels_view.datastore = datastore
        
        add_channel_view = self.ids.addChannelView
        add_channel_view.bind(on_channel_added=self.channel_added)
        add_channel_view.settings = settings
        add_channel_view.datastore = datastore
        
        self.register_event_type('on_channels_customized')
        
    def on_channels_customized(self, *args):
        pass

    def channel_removed(self, *args):
        pass
    
    def channel_added(self, *args):
        pass        
        
class CurrentChannelsView(Screen):    
    def __init__(self, **kwargs):
        super(CurrentChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_channel_removed')
            
    def on_channel_removed(self, *args):
        pass
    
class AddChannelView(Screen):
    settings = None
    datastore = None
    def __init__(self, **kwargs):
        super(AddChannelView, self).__init__(**kwargs)
        self.register_event_type('on_channel_added')
        
    def on_channel_added(self, *args):
        pass
    