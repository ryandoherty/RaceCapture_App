import kivy
kivy.require('1.8.0')
from iconbutton import IconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.listview import ListView, ListItemButton
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter

Builder.load_file('autosportlabs/racecapture/views/analysis/addstreamview.kv')

class AddStreamView(FloatLayout):
    channel = None
    settings = None
    def __init__(self, **kwargs):
        super(AddStreamView, self).__init__(**kwargs)
        self.register_event_type('on_stream_selected')
        
        self.settings = kwargs.get('settings')

    def on_stream_selected(self, selected_channel):
        pass
        