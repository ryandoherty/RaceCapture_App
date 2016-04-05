#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
#have received a copy of the GNU General Public License along with
#this code. If not, see <http://www.gnu.org/licenses/>.
import os
from threading import Thread
import kivy
kivy.require('1.9.1')
from kivy.logger import Logger
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
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from iconbutton import IconButton
from fieldlabel import FieldLabel

Builder.load_file('autosportlabs/racecapture/views/analysis/customizechannelsview.kv')

    
class CustomizeChannelsView(BoxLayout):
    def __init__(self, **kwargs):
        super(CustomizeChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_channels_customized')
        self.datastore = kwargs.get('datastore')
        channels = kwargs.get('current_channels')
        
        screen_manager = self.ids.screens
        screen_manager.transition = SwapTransition()
        add_channels_view =  AddChannelsView(name='add')
        current_channels_view = CurrentChannelsView(name='current')
        current_channels_view.bind(on_confirm_customize=self.confirm_customize)
        current_channels_view.bind(on_add_channels=self.add_channels)
        current_channels_view.channels = channels
        add_channels_view.bind(on_go_back=self.add_channels_complete)
        
        self.current_channels_view = current_channels_view
        self.add_channels_view = add_channels_view
        
        screen_manager.add_widget(current_channels_view)
        screen_manager.add_widget(add_channels_view)
        if not len(channels):
            self.add_channels()

    def confirm_customize(self, *args):
        self.dispatch('on_channels_customized', self.current_channels_view.channels)
        
    def _get_available_channel_names(self):
        available_channels = self.datastore.channel_list
        channels = [str(c) for c in available_channels]
        return channels
     
    def add_channels(self, *args):
        available_channels = self._get_available_channel_names()
        current_channels = self.current_channels_view.channels
        add_channels = [c for c in available_channels if c not in current_channels]
        self.add_channels_view.available_channels = add_channels        
        self.ids.screens.current = 'add'
                
    def add_channels_complete(self, instance, added_channels):
        self.ids.screens.current = 'current'
        current_channels = self.current_channels_view.channels
        current_channels.extend(added_channels)
        if len(current_channels) == len(added_channels):
            self.confirm_customize()
        
        
    def on_channels_customized(self, *args):
        pass
    
class CurrentChannel(BoxLayout):
    channel = None

    def __init__(self, **kwargs):
        super(CurrentChannel, self).__init__(**kwargs)
        self.channel = kwargs.get('channel')
        self.register_event_type('on_delete_channel')
        self.register_event_type('on_modified')
        self.ids.name.text = self.channel

    def on_modified(self):
        pass
                
    def on_delete_channel(self, channel):
        pass
    
    def on_delete(self):
        self.dispatch('on_delete_channel', self.channel)
    
class CurrentChannelsView(Screen):
    channels = ListProperty()
    _current_channel_widgets = {}
    
    def __init__(self, **kwargs):
        super(CurrentChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_confirm_customize')
        self.register_event_type('on_add_channels')
        
    def on_channels(self, instance, value):
        grid = self.ids.current_channels
        grid.clear_widgets()
        self._current_channel_widgets.clear()
        for channel in value:
            current_channel = CurrentChannel(channel = channel)
            current_channel.bind(on_delete_channel=self.on_delete_channel)
            current_channel.bind(on_modified=self.on_modified)
            grid.add_widget(current_channel)
            self._current_channel_widgets[channel] = current_channel
            
    def on_delete_channel(self, instance, name):
        try:
            grid = self.ids.current_channels
            widget = self._current_channel_widgets.get(name)
            grid.remove_widget(widget)
            self.channels.remove(name)
        except Exception as e:
            Logger.error('Error deleting channel ' + name + ': ' + str(name))
        
    
    def on_modified(self, instance, name):
        print("modified " + name)   
        
    def on_confirm_customize(self, *args):
        pass
    
    def on_add_channels(self, *args):
        pass
    
    def confirm_customize(self, *args):
        self.dispatch('on_confirm_customize')
    
    def add_channels(self, *args):
        self.dispatch('on_add_channels')
        
class AddChannelsView(Screen):
    added_channels = ListProperty()
    available_channels = ListProperty()
    
    def __init__(self, **kwargs):
        super(AddChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_go_back')
        self.ids.add_channels.bind(on_channel_selected=self.channel_selected)

    def on_added_channels(self, instance, value):
        pass

    def on_pre_enter(self):
        del self.added_channels[:]
        del self.ids.add_channels.channels[:]
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
        
