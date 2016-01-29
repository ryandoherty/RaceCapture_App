import kivy
kivy.require('1.9.0')
from kivy.logger import Logger
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.anchorlayout import AnchorLayout
from iconbutton import IconButton
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from autosportlabs.racecapture.views.analysis.customizechannelsview import CustomizeChannelsView
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty, ObjectProperty
Builder.load_file('autosportlabs/racecapture/views/analysis/analysiswidget.kv')
    
class OptionsButton(AnchorLayout):
    pass

class AnalysisWidget(AnchorLayout):
    """
    The base for all analysis UI widgets
    
    This base class can handle the addition / removal of laps selected for viewing.
    Selected laps are the basis for determining what data is displayed in a particular widget.
    
    Extend this class directly when you want to create a widget that specifically controls the data to be displayed, such as
    the analysis map.
    """
    options_enabled = BooleanProperty(None)
    
    def __init__(self, **kwargs):
        super(AnalysisWidget, self).__init__(**kwargs)
        self.settings = None
        self.datastore = None
        self.selected_laps = {}
        self.settings = kwargs.get('settings')
        self.datastore = kwargs.get('datastore')
        Clock.schedule_once(lambda dt: self.add_option_buttons())
        
    def add_option_buttons(self):
        '''
        Override this to add additional buttons to the widget's floating toolbar
        '''
        pass
    
    def append_option_button(self, button):
        self.ids.options_bar.add_widget(button)
        
    def on_options_enabled(self, instance, value):
        if value == False:
            self.remove_widget(self.ids.options_button)
        else:
            options = self.ids.options_button
            self.remove_widget(options)
            self.add_widget(options)

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
    """
    A base widget that can select one or more channels to display.
    
    Extend this class if you want to make a general purpose widget that shows one or more channels.
    """
    sessions = ObjectProperty(None)
    DEFAULT_CHANNELS = ["Speed"]
    
    def __init__(self, **kwargs):
        super(ChannelAnalysisWidget, self).__init__(**kwargs)
        self._popup = None
        self._selected_channels = []
        self.register_event_type('on_channel_selected')

    def on_sessions(self, instance, value):
        self.refresh_view()
        
    def on_lap_added(self, lap_ref):
        if len(self._selected_channels) == 0:
            self._selected_channels = list(self.DEFAULT_CHANNELS)
        self.add_channels(self._selected_channels, lap_ref)
    
    def on_lap_removed(self, lap_ref):
        for channel in self._selected_channels:
            self.remove_channel(channel, lap_ref)
        self.refresh_view()

    def on_channel_selected(self, value):
        pass
    
    def add_channels(self, channels, lap_ref):
        '''
        Override this to add a channel / lap reference combo to the view
        '''
        pass
    
    def remove_channel(self, channel, lap_ref):
        '''
        Override this function to remove a channel / lap reference combo from the view
        '''
        pass

    def refresh_view(self):
        '''
        Override this to refresh / re-draw the view
        '''
        pass

    def _add_channels_all_laps(self, channels):
        for lap_ref in self.selected_laps.itervalues():
            self.add_channels(channels, lap_ref)

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
        self._add_channels_all_laps(added)
            
    def select_channels(self, selected_channels):
        self.merge_selected_channels(selected_channels)

    def _channels_customized(self, instance,  updated_channels):
        self._dismiss_popup()
        self.select_channels(updated_channels)
        self.dispatch('on_channel_selected', updated_channels)

    def on_options(self, *args):
        self.show_customize_dialog()
            
    def show_customize_dialog(self):
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
    