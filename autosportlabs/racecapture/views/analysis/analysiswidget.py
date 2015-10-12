import kivy
kivy.require('1.9.0')
from kivy.logger import Logger
from kivy.app import Builder
from kivy.uix.anchorlayout import AnchorLayout
from iconbutton import IconButton
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from autosportlabs.racecapture.views.analysis.customizechannelsview import CustomizeChannelsView
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty
Builder.load_file('autosportlabs/racecapture/views/analysis/analysiswidget.kv')

class ChannelData(object):
    data = None
    channel = None
    min = 0
    max = 0
    source = None
    
    def __init__(self, **kwargs):
        self.data = kwargs.get('data', None)
        self.channel = kwargs.get('channel', None)
        self.min = kwargs.get('min', 0)
        self.max = kwargs.get('max', 0)
        self.source = kwargs.get('source', None)
    
class AnalysisWidget(AnchorLayout):
    """ The base analysis widget that can receive lap added / removed events
    """
    def __init__(self, **kwargs):
        super(AnalysisWidget, self).__init__(**kwargs)
        self.settings = None
        self.datastore = None
        self.selected_laps = {}
        self.settings = kwargs.get('settings')
        self.datastore = kwargs.get('datastore')
    
    def on_options(self, *args):
        pass

    def on_lap_added(self, lap_ref):
        pass
    
    def on_lap_removed(self, lap_ref):
        pass
        
    def add_lap(self, lap_ref):
        self.selected_laps[str(lap_ref)] = lap_ref
        self.on_lap_added(lap_ref)
    
    def remove_lap(self, lap_ref):
        try:
            self.on_lap_removed(lap_ref)
            del(self.selected_laps[str(lap_ref)])
        except Exception as e:
            Logger.error("AnalysisWidget: Error removing remove lap " + str(e))

class ChannelAnalysisWidget(AnalysisWidget):
    """A widget that can select it's own channels to display
    """
    options_enabled = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        super(ChannelAnalysisWidget, self).__init__(**kwargs)
        self._popup = None
        self._selected_channels = []
        self.register_event_type('on_channel_selected')

    def on_lap_added(self, lap_ref):
        for channel in self._selected_channels:
            self.query_new_channel(channel, lap_ref)
    
    def on_lap_removed(self, lap_ref):
        for channel in self._selected_channels:
            self.remove_channel(channel, lap_ref)
        self.refresh_view()

    def on_options_enabled(self, instance, value):
        if value == False:
            self.remove_widget(self.ids.options_button)

    def on_channel_selected(self, value):
        pass
    
    def add_channel(self, channel_data):
        pass
    
    def remove_channel(self, channel, ref):
        pass

    def query_new_channel_all_laps(self, channel):
        for lap_ref in self.selected_laps.itervalues():
            self.query_new_channel(channel, lap_ref)

    def query_new_channel(self, channel, lap_ref):
        pass
        
    def refresh_view(self):
        pass

    def _remove_channel_all_laps(self, channel):
        for k,v in self.selected_laps.iteritems():
            self.remove_channel(channel, k)
        self.refresh_view()

    def merge_selected_channels(self, updated_channels):
        current = self._selected_channels
        removed = [c for c in current if c not in updated_channels]
        added = [c for c in updated_channels if c not in current]
                
        for c in removed:
            current.remove(c)
            self._remove_channel_all_laps(c)

        for c in added:
            current.append(c)
            self.query_new_channel_all_laps(c)
            
    def _channels_customized(self, instance,  updated_channels):
        self._dismiss_popup()
        self.merge_selected_channels(updated_channels)
        self.dispatch('on_channel_selected', updated_channels)
            
    def on_options(self, *args):
        self.showCustomizeDialog()
            
    def showCustomizeDialog(self):
        content = CustomizeChannelsView(settings=self.settings, datastore=self.datastore, current_channels=self._selected_channels)
        content.bind(on_channels_customized=self._channels_customized)

        popup = Popup(title="Customize Channels", content=content, size_hint=(0.7, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
            
    def popup_dismissed(self, *args):
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None
    