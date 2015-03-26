import kivy
from channels import *
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from utils import *
from autosportlabs.racecapture.views.configuration.channels.channelsview import ChannelEditor

Builder.load_file('channelnameselectorview.kv')

class ChannelNameSelectorView(BoxLayout):
    channel_type = NumericProperty(CHANNEL_TYPE_UNKNOWN)
    channel_config = None
    runtime_channels = None
    
    def __init__(self, **kwargs):
        super(ChannelNameSelectorView, self).__init__(**kwargs)
        self.register_event_type('on_channels_updated')        
        self.register_event_type('on_channel')
        self.bind(channel_type = self.on_channel_type)

    def on_channels_updated(self, runtime_channels):
        self.runtime_channels = runtime_channels
        kvFind(self, 'rcid', 'id').dispatch('on_channels_updated', runtime_channels)        
    
    def on_channel_type(self, instance, value):
        spinner = kvFind(self, 'rcid', 'id')
        spinner.channelType = value
    
    def setValue(self, value):
        self.channel_config = value
        self.set_channel_name(value.name)

    def set_channel_name(self, name):
        spinner = kvFind(self, 'rcid', 'id')
        spinner.text = str(name)
        
    def on_channel_selected(self, instance, value):
        channel_meta = self.runtime_channels.findChannelMeta(value, None)
        if channel_meta is not None:
            self.channel_config.name = channel_meta.name
            self.channel_config.units = channel_meta.units
            self.channel_config.min = channel_meta.min
            self.channel_config.max = channel_meta.max
            self.channel_config.precision = channel_meta.precision
            self.dispatch('on_channel')
    
    def _dismiss_editor(self):
        self._popup.dismiss()
        
    def on_customize(self, *args):
        
        content = ChannelEditor(channel = self.channel_config)
        popup = Popup(title = 'Customize Channel',
                      content = content, 
                      size_hint=(None, None), size = (dp(500), dp(220)))
        popup.bind(on_dismiss=self.on_edited)
        content.bind(on_channel_edited=lambda *args:popup.dismiss())                     
        popup.open()
    
    def on_edited(self, *args):
        self.set_channel_name(self.channel_config.name)
        self.dispatch('on_channel')
        
    def on_channel(self):
        pass
        
        