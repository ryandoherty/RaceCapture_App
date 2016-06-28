import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from settingsview import SettingsView, SettingsTextField, SettingsSwitch

Builder.load_string('''
<BackgroundStreamingView>
    size_hint_y: None
    height: dp(80)
    SettingsView:
        id: bgStream
        label_text: 'Background Streaming'
        help_text: 'Stream real-time telemetry continuously in the background'
    HelpLabel:
        text: 'When disabled, telemetry is synchronized with SD logging.'
        halign: 'left'
''')


class BackgroundStreamingView(BaseConfigView):

    def __init__(self, **kwargs):
        self.connectivityConfig = None
        super(BackgroundStreamingView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')

    def on_bg_stream(self, instance, value):
        Logger.info("BackgroundStreamingView: on_bg_stream")
        if self.connectivityConfig:
            self.connectivityConfig.telemetryConfig.backgroundStreaming = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')

    def on_config_updated(self, rcpCfg):

        self.connectivityConfig = rcpCfg.connectivityConfig

        bg_stream_switch = self.ids.bgStream
        bg_stream_switch.setControl(SettingsSwitch(active=self.connectivityConfig.telemetryConfig.backgroundStreaming))
        bg_stream_switch.control.bind(active=self.on_bg_stream)

