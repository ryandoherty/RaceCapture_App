import os
from threading import Thread
import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.clock import Clock
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.screenmanager import Screen, SwapTransition
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter
from iconbutton import IconButton
from autosportlabs.uix.button.featurebutton import FeatureButton
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectorView
from iconbutton import IconButton

Builder.load_file('autosportlabs/racecapture/views/analysis/customizechannelsview.kv')

class CustomizeResult(object):
    add_channels_view = []
    remove_channels = []    
    def __init__(self, **kwargs):
        self.add_channels_view = kwargs.get("add_channels_view", [])
        self.remove_channels  = kwargs.get("remove_channels", [])
    
class CustomizeChannelsView(BoxLayout):
    customize_results = CustomizeResult()
    
    def __init__(self, **kwargs):
        super(CustomizeChannelsView, self).__init__(**kwargs)
        datastore = kwargs.get('datastore')
        channels = kwargs.get('current_channels')
        
        screen_manager = self.ids.screens
        screen_manager.transition = SwapTransition()
        add_channels_view =  AddChannelsView(name='add')
        current_channels_view = CurrentChannelsView(name='current')
        screen_manager.add_widget(current_channels_view)
        screen_manager.add_widget(add_channels_view)

        current_channels_view.channels = channels
        add_channels_view.available_channels = datastore.channel_list
        add_channels_view.bind(on_go_back=self.hide_add_channels)
        
        self.register_event_type('on_channels_customized')
        self.current_channels_view = current_channels_view
        self.add_channels_view = add_channels_view
        screen_manager.current = 'add'
        
    def hide_add_channels(self, instance, value):
        self.ids.screens.current = 'current'
        print(str(value))
        
    def on_channels_customized(self, instance, value):
        pass

    def channel_removed(self, instance, value):
        self.customize_results.remove_channels.append(value)
    
    def channel_added(self, instance, value):
        self.customize_results.add_channels_view.append(value)        
    
class CurrentChannelsView(Screen):
    current_channels_view = ListProperty()
    removed_channels = ListProperty()
    
    def __init__(self, **kwargs):
        super(CurrentChannelsView, self).__init__(**kwargs)
        
    def on_current_channels(self, instance, value):
        pass
        
class AddChannelsView(Screen):
    added_channels = ListProperty()
    available_channels = ListProperty()
    
    def __init__(self, **kwargs):
        super(AddChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_go_back')

    def on_added_channels(self, instance, value):
        pass
    
    def on_available_channels(self, instance, value):
        self.ids.add_channels.bind(on_channel_selected=self.channel_selected)
        self.ids.add_channels.channels = self.available_channels
        
    def on_go_back(self, channels):
        pass
    
    def go_back(self, *args):
        self.dispatch('on_go_back', [])
        
    def channel_selected(self, instance, value):
        self.added_channels=value[:]
        self.ids.confirm.disabled = False
        
    def confirm_add(self, *args):
        self.dispatch('on_go_back', self.added_channels[:])
        
