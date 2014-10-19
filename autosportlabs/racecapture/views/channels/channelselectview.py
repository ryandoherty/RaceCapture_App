import kivy
kivy.require('1.8.0')
from iconbutton import IconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.listview import ListView, ListItemButton
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter

Builder.load_file('autosportlabs/racecapture/views/channels/channelselectview.kv')

class ChannelItemButton(ListItemButton):
    def __init__(self, **kwargs):
        super(ChannelItemButton, self).__init__(**kwargs)

class ChannelSelectView(FloatLayout):
    def __init__(self, **kwargs):
        super(ChannelSelectView, self).__init__(**kwargs)
        self.register_event_type('on_channel_selected')
        self.register_event_type('on_channel_cancel')
        
        settings = kwargs.get('settings')
        type = kwargs.get('type')
        
        data = []
        channelList = self.ids.channelList
        for channel,channelMeta in settings.systemChannels.channels.iteritems():
            channelType = channelMeta.type
            #if channelType == type or channelType == None:
            data.append({'text': channel, 'is_selected': False})    

        args_converter = lambda row_index, rec: {'text': rec['text'], 'size_hint_y': None, 'height': dp(50)}

        list_adapter = ListAdapter(data=data,
                           args_converter=args_converter,
                           cls=ChannelItemButton,
                           selection_mode='single',
                           allow_empty_selection=False)

        channelList.adapter=list_adapter
        list_adapter.bind(on_selection_change=self.on_select)

    def on_select(self, value):
        self.dispatch('on_channel_selected', value.selection[0].text)
    
    def on_cancel(self):
        self.dispatch('on_channel_cancel')
        pass

    def on_channel_selected(self, selectedTrackIds):
        pass
    
    def on_channel_cancel(self):
        pass
    