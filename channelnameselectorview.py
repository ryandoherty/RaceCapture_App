import kivy
from channels import *
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.properties import NumericProperty
from utils import *

Builder.load_file('channelnameselectorview.kv')

class ChannelNameSelectorView(BoxLayout):
    channel_type = NumericProperty(CHANNEL_TYPE_UNKNOWN)
    channel_config = None
    
    def __init__(self, **kwargs):
        super(ChannelNameSelectorView, self).__init__(**kwargs)
        self.register_event_type('on_channels_updated')        
        self.register_event_type('on_channel')
        self.bind(channel_type = self.on_channel_type)

    def on_channels_updated(self, system_channels):
        kvFind(self, 'rcid', 'id').dispatch('on_channels_updated', system_channels)        
    
    def on_channel_type(self, instance, value):
        spinner = kvFind(self, 'rcid', 'id')
        spinner.channelType = value
    
    def setValue(self, value):
        self.channel_config = value
        spinner = kvFind(self, 'rcid', 'id')
        spinner.text = str(value.name)

    def onSelect(self, instance, value):
        self.dispatch('on_channel', value)
    
    def on_customize(self, *args):
        pass
    
    def on_channel(self, value):
        pass
        
        