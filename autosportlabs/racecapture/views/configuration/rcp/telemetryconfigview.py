import kivy
kivy.require('1.9.0')
from kivy.app import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
import re
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.uix.toast.kivytoast import toast
from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble, WarnLabel
from autosportlabs.widgets.separator import HLineSeparator
from settingsview import SettingsView, SettingsTextField, SettingsSwitch
from valuefield import ValueField
from kivy.metrics import dp
from utils import *

TELEMETRY_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/telemetryconfigview.kv'
WARN_DISMISS_TIMEOUT = 7.24

class TelemetryConfigView(BaseConfigView):
    connectivityConfig = None

    def __init__(self, **kwargs):    
        Builder.load_file(TELEMETRY_CONFIG_VIEW_KV)
        super(TelemetryConfigView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
    
        deviceId = kvFind(self, 'rcid', 'deviceId') 
        deviceId.bind(on_setting=self.on_device_id)
        deviceId.setControl(SettingsTextField())
        
        bgStream = kvFind(self, 'rcid', 'bgStream')
        bgStream.bind(on_setting=self.on_bg_stream)
        bgStream.setControl(SettingsSwitch())
        
    def on_device_id(self, instance, value):
        if self.connectivityConfig:
            value = strip_whitespace(value)
            if len(value) > 0:
                if self.validate_device_id(value):
                    instance.setValue(value)
                    self.connectivityConfig.telemetryConfig.deviceId = value
                    self.connectivityConfig.stale = True
                    self.dispatch('on_modified')
                else:
                    warn = CenteredBubble()
                    warn.add_widget(WarnLabel(text=str('Id may contain only numbers and letters')))
                    warn.auto_dismiss_timeout(WARN_DISMISS_TIMEOUT)
                    warn.background_color = (1, 0, 0, 1.0)
                    warn.size = (dp(300), dp(50))
                    warn.size_hint = (None,None)
                    self.get_root_window().add_widget(warn)
                    warn.center_below(instance.control)


    def on_bg_stream(self, instance, value):
        if self.connectivityConfig:
            self.connectivityConfig.telemetryConfig.backgroundStreaming = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')
                
    def on_config_updated(self, rcpCfg):
        connectivityConfig = rcpCfg.connectivityConfig
        kvFind(self, 'rcid', 'bgStream').setValue(connectivityConfig.telemetryConfig.backgroundStreaming)
        kvFind(self, 'rcid', 'deviceId').setValue(connectivityConfig.telemetryConfig.deviceId)
        self.connectivityConfig = connectivityConfig

    def validate_device_id(self, device_id):
        return device_id.isalnum()
