import kivy
kivy.require('1.8.0')
from iconbutton import IconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from fieldlabel import FieldLabel

Builder.load_file('autosportlabs/racecapture/views/channels/channelcustomizationview.kv')

class ChannelCustomizationView(FloatLayout):
    def __init__(self, **kwargs):
        self.settings = None
        self.channel = None
        super(ChannelCustomizationView, self).__init__(**kwargs)
        self.register_event_type('on_channel_customization_close')
        
        self.settings = kwargs.get('settings')
        self.channel = kwargs.get('channel')
    
    def on_close(self):
        self.dispatch('on_channel_customization_close')
        pass

    def on_channel_customization_close(self):
        pass
        