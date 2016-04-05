import kivy
kivy.require('1.9.1')
from kivy.uix.spinner import Spinner

class ChannelNameSpinner(Spinner):
    channelType = None
    filterList = None
    def __init__(self, **kwargs):
        super(ChannelNameSpinner, self).__init__(**kwargs)
        self.register_event_type('on_channels_updated')
        self.values = []
     
    def on_channels_updated(self, runtime_channels):
        channel_names = runtime_channels.channel_names
        filtered_channel_names = channel_names
        if self.filterList != None:
            filtered_channel_names = []
            filter_list = self.filterList
            for channel in channel_names:
                if channel in filter_list:
                    filtered_channel_names.append(channel)
                    
        self.values = filtered_channel_names
