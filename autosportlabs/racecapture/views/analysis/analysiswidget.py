import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.anchorlayout import AnchorLayout
from iconbutton import IconButton
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from kivy.uix.popup import Popup
Builder.load_file('autosportlabs/racecapture/views/analysis/analysiswidget.kv')

class AnalysisWidget(AnchorLayout):
    settings = None

    def __init__(self, **kwargs):
        super(AnalysisWidget, self).__init__(**kwargs)
        self.settings = kwargs.get('settings')
    
    def on_options(self, *args):
        pass    

class ChannelAnalysisWidget(AnalysisWidget):
    _popup = None
    def __init__(self, **kwargs):
        super(ChannelAnalysisWidget, self).__init__(**kwargs)
        self.register_event_type('on_channel_selected')
    
    def on_channel_selected(self, value):
        pass
    
    def on_options(self, *args):
        self.showChannelSelectDialog()
        
    def showChannelSelectDialog(self):
        content = ChannelSelectView(settings=self.settings)
        content.bind(on_channel_selected=self.channel_selected)
        content.bind(on_channel_cancel=self._dismiss_popup)

        popup = Popup(title="Select Channel", content=content, size_hint=(0.5, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
    
    def channel_selected(self, instance, value):
        self.dispatch('on_channel_selected', value)
        self._dismiss_popup()

    def popup_dismissed(self, *args):
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None
    