import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.anchorlayout import AnchorLayout
from iconbutton import IconButton
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from kivy.uix.popup import Popup
Builder.load_file('autosportlabs/racecapture/views/analysis/analysiswidget.kv')

class AnalysisWidget(AnchorLayout):
    _popup = None
    channel = None
    settings = None
    def __init__(self, **kwargs):
        super(AnalysisWidget, self).__init__(**kwargs)
        self.settings = kwargs.get('settings')
        self.register_event_type('on_channel_selected')
    
    def on_channel_selected(self, value):
        pass
    
    def on_options(self, *args):
        self.showChannelSelectDialog()
        
    def _init_view(self):
        options_button=IconButton(text='|', id='options', on_press=self.on_options)
        self.add_widget(options_button)
        
        
    def showChannelSelectDialog(self):
        content = ChannelSelectView(settings=self.settings, channel=self.channel)
        content.bind(on_channel_selected=self.channel_selected)
        content.bind(on_channel_cancel=self._dismiss_popup)

        popup = Popup(title="Select Channel", content=content, size_hint=(0.5, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        #self._dismiss_customization_popup_trigger()
        
    
    def channel_selected(self, instance, value):
        print("channel " + value)
        self.dispatch('on_channel_selected', value)
        self._dismiss_popup()

    def popup_dismissed(self, *args):
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None
    