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
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.screenmanager import Screen, SwapTransition
from kivy.uix.button import ButtonBehavior
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

KV_FILE="""
<CustomizeChannelsView>:
    BoxLayout:
        orientation: 'vertical'
        ScrollContainer:
            id: scroller
            size_hint_y: 1.0
            do_scroll_x:False
            do_scroll_y:True
            GridLayout:
                spacing: sp(5)
                id: current_channels
                row_default_height: root.height * 0.18
                row_force_default: True
                size_hint_y: None
                height: max(self.minimum_height, scroller.height)
                cols: 1

<BaseChannelSelection>:
    spacing: sp(5)
    padding: [0, 0, 0, sp(5)]
    size_hint_y: None
    orientation: 'horizontal'

<CurrentChannel>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_primary()
        Rectangle:
            pos: self.pos
            size: self.size
    FieldLabel:
        halign: 'center'
        id: name
        size_hint_x: 0.9
        font_size: root.height * 0.6
    IconButton:
        size_hint_x: 0.1
        size_hint_y: 0.9
        text: '\357\200\224'
        on_release: root.on_delete()

<AddChannel>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_dark_background_translucent()
        Rectangle:
            pos: self.pos
            size: self.size
    FieldLabel:
        id: name
        halign: 'center'
        size_hint_x: 0.9
        font_size: root.height * 0.6
    BoxLayout:
        size_hint_x: 0.1
"""
    
class CustomizeChannelsView(BoxLayout):
    Builder.load_string(KV_FILE)

    def __init__(self, **kwargs):
        super(CustomizeChannelsView, self).__init__(**kwargs)
        self._channel_widgets = {}
        self.register_event_type('on_channels_customized')
        self.datastore = kwargs.get('datastore')
        self._current_channels = kwargs.get('current_channels')
        self._refresh_channel_list()
        
    def _refresh_channel_list(self):
        grid = self.ids.current_channels
        grid.clear_widgets()        
        self._add_selected_channels(self._current_channels)
        self._add_unselected_channels(self._current_channels)

    def _get_available_channel_names(self):
        available_channels = self.datastore.channel_list
        channels = [str(c) for c in available_channels]
        return channels

    def on_delete_channel(self, instance, name):
        try:
            grid = self.ids.current_channels
            widget = self._channel_widgets.get(name)
            grid.remove_widget(widget)
            self._current_channels.remove(name)
            self._refresh_channel_list()
            self.dispatch('on_channels_customized', self._current_channels)
        except Exception as e:
            Logger.error('Error deleting channel ' + name + ': ' + str(name))

    def on_add_channel(self, instance, name):
        self._current_channels.append(name)
        self._refresh_channel_list()
        self.dispatch('on_channels_customized', self._current_channels)

    def _add_selected_channels(self, current_channels):
        grid = self.ids.current_channels
        self._channel_widgets.clear()
        for channel in sorted(current_channels):
            current_channel = CurrentChannel(channel = channel)
            current_channel.bind(on_delete_channel=self.on_delete_channel)
            grid.add_widget(current_channel)
            self._channel_widgets[channel] = current_channel

    def _add_unselected_channels(self, current_channels):
        available_channels = self._get_available_channel_names()
        add_channels = [c for c in available_channels if c not in current_channels]
        grid = self.ids.current_channels
        for channel in sorted(add_channels):
            add_channel = AddChannel(channel = channel)
            add_channel.bind(on_add_channel=self.on_add_channel)
            grid.add_widget(add_channel)

    def on_channels_customized(self, *args):
        pass
    
class BaseChannelSelection(BoxLayout):
    pass

class CurrentChannel(BaseChannelSelection):
    channel = None

    def __init__(self, **kwargs):
        super(CurrentChannel, self).__init__(**kwargs)
        self.channel = kwargs.get('channel')
        self.register_event_type('on_delete_channel')
        self.ids.name.text = self.channel

    def on_modified(self, *args):
        pass
                
    def on_delete_channel(self, channel):
        pass
    
    def on_delete(self):
        self.dispatch('on_delete_channel', self.channel)

class AddChannel(ButtonBehavior, BaseChannelSelection):
    channel = None

    def __init__(self, **kwargs):
        super(AddChannel, self).__init__(**kwargs)
        self.channel = kwargs.get('channel')
        self.register_event_type('on_add_channel')
        self.ids.name.text = self.channel

    def on_release(self, *args):
        self.dispatch('on_add_channel', self.channel)
        
    def on_modified(self, *args):
        pass

    def on_add_channel(self, channel):
        pass

    def on_add(self):
        self.dispatch('on_add_channel', self.channel)
