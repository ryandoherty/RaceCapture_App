import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
import re
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.views.configuration.rcp.telemetry.backgroundstreamingview import BackgroundStreamingView
from autosportlabs.widgets.separator import HLineSeparator
from settingsview import SettingsView, SettingsTextField, SettingsSwitch
from valuefield import ValueField
from utils import *

TELEMETRY_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/telemetry/telemetryconfigview.kv'


class TelemetryConfigView(BaseConfigView):
    connectivityConfig = None
    Builder.load_file(TELEMETRY_CONFIG_VIEW_KV)

    def __init__(self, capabilities, **kwargs):
        super(TelemetryConfigView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
    
        deviceId = kvFind(self, 'rcid', 'deviceId')
        deviceId.bind(on_setting=self.on_device_id)
        deviceId.setControl(SettingsTextField())

        self._bg_stream_view = None
        self.capabilities = capabilities

        self._render()

    def _render(self):
        if self.capabilities.has_cellular:
            separator = HLineSeparator()
            self.ids.content.add_widget(separator)

            bg_stream_view = BackgroundStreamingView()
            self.ids.content.add_widget(bg_stream_view)
            bg_stream_view.bind(on_modified=self._on_bg_stream_modified)
            self._bg_stream_view = bg_stream_view

    def _on_bg_stream_modified(self, *args):
        self.dispatch('on_config_modified')

    def on_device_id(self, instance, value):
        if self.connectivityConfig and value != self.connectivityConfig.telemetryConfig.deviceId:
            value = strip_whitespace(value)
            if len(value) > 0 and not self.validate_device_id(value):
                instance.set_error('Only numbers / letters allowed')
            else:
                #instance.setValue(value)
                self.connectivityConfig.telemetryConfig.deviceId = value
                self.connectivityConfig.stale = True
                self.dispatch('on_modified')
                instance.clear_error()

    def on_config_updated(self, rcpCfg):
        connectivityConfig = rcpCfg.connectivityConfig
        kvFind(self, 'rcid', 'deviceId').setValue(connectivityConfig.telemetryConfig.deviceId)
        self.connectivityConfig = connectivityConfig

        if self._bg_stream_view:
            self._bg_stream_view.on_config_updated(rcpCfg)

    def validate_device_id(self, device_id):
        return device_id.isalnum()
