import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.anchorlayout import AnchorLayout
from iconbutton import IconButton
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from autosportlabs.racecapture.views.analysis.customizechannelsview import CustomizeChannelsView
from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from kivy.uix.popup import Popup
Builder.load_file('autosportlabs/racecapture/views/analysis/analysiswidget.kv')

class ChannelData(object):
    records = None
    channel = None
    min = 0
    max = 0
    source = None
    
    def __init__(self, **kwargs):
        self.records = kwargs.get('records', None)
        self.channel = kwargs.get('channel', None)
        self.min = kwargs.get('min', 0)
        self.max = kwargs.get('max', 0)
        self.source = kwargs.get('source', None)
    
class AnalysisWidget(AnchorLayout):
    settings = None
    datastore = None
    def __init__(self, **kwargs):
        super(AnalysisWidget, self).__init__(**kwargs)
        self.settings = kwargs.get('settings')
        self.datastore = kwargs.get('datastore')
    
    def on_options(self, *args):
        pass    

class ChannelAnalysisWidget(AnalysisWidget):
    _popup = None
    _selected_channels = []
    
    def __init__(self, **kwargs):
        super(ChannelAnalysisWidget, self).__init__(**kwargs)
        self.register_event_type('on_channel_selected')
    
    def on_channel_selected(self, value):
        pass
    
    def on_options(self, *args):
        self.showCustomizeDialog()
        
    def showCustomizeDialog(self):
        content = CustomizeChannelsView(settings=self.settings, datastore=self.datastore, current_channels=self._selected_channels)
        content.bind(on_channels_customized=self.channels_customized)

        popup = Popup(title="Customize Channels", content=content, size_hint=(0.7, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
    
    def query_new_channel(self, channel):
        lap = 3
        session = 1
        f = Filter().eq('LapCount', lap)
        dataset = self.datastore.query(sessions=[session],
                         channels=['Distance', channel], data_filter=f)
        
        records = dataset.fetch_records()
        source = SourceRef(lap, session)
        channel_data = ChannelData(records=records, channel=channel, min=0, max=255, source=source)
        self.add_channel(channel_data)
    
    def add_channel(self, channel_data):
        pass
    
    def remove_channel(self, channel):
        pass
    
    def merge_selected_channels(self, updated_channels):
        current = self._selected_channels
        removed = [c for c in current if c not in updated_channels]
        added = [c for c in updated_channels if c not in current]
                
        for c in removed:
            current.remove(c)
            self.remove_channel(c)

        for c in added:
            current.append(c)
            self.query_new_channel(c)
            
    def channels_customized(self, instance,  updated_channels):
        self._dismiss_popup()
        self.merge_selected_channels(updated_channels)
        for channel in updated_channels:
            self.dispatch('on_channel_selected', channel)

    def popup_dismissed(self, *args):
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None
    