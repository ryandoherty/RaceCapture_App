import kivy
kivy.require('1.9.0')
from autosportlabs.uix.iconbutton import TileIconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.listview import ListView, ListItemButton
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter
from kivy.logger import Logger

Builder.load_file('autosportlabs/racecapture/views/channels/channelselectview.kv')

class ChannelItemButton(ListItemButton):
    def __init__(self, **kwargs):
        super(ChannelItemButton, self).__init__(**kwargs)

class ChannelSelectView(FloatLayout):
    channel = None
    def __init__(self, **kwargs):
        super(ChannelSelectView, self).__init__(**kwargs)
        self.register_event_type('on_channel_selected')
        self.register_event_type('on_channel_cancel')
        
        settings = kwargs.get('settings')
        type = kwargs.get('type')
        channel = kwargs.get('channel')
        
        data = []
        channel_list = self.ids.channelList
        try:
            for available_channel,channelMeta in settings.runtimeChannels.channels.iteritems():
                channel_type = channelMeta.type
                data.append({'text': available_channel, 'is_selected': False})
                
            args_converter = lambda row_index, rec: {'text': rec['text'], 'size_hint_y': None, 'height': dp(50)}
    
            list_adapter = ListAdapter(data=data,
                               args_converter=args_converter,
                               cls=ChannelItemButton,
                               selection_mode='single',
                               allow_empty_selection=True)
    
            channel_list.adapter=list_adapter
            list_adapter.bind(on_selection_change=self.on_select)
            self.channel = channel
        except Exception as e:
            Logger.error("ChannelSelectView: Error initializing: " + str(e))
    
    def on_select(self, value):
        try:
            self.channel = value.selection[0].text
        except Exception as e:
            Logger.error('ChannelSelectView: Error Selecting channel: ' + str(e))
    
    def on_close(self):
        self.dispatch('on_channel_selected', self.channel)

    def on_channel_selected(self, selected_channel):
        pass
    
    def on_channel_cancel(self):
        pass
    