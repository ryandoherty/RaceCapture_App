import kivy
kivy.require('1.9.0')
from kivy.app import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
import re


from settingsview import SettingsView, SettingsTextField, SettingsSwitch
from autosportlabs.widgets.separator import HLineSeparator
from valuefield import ValueField
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView

TELEMETRY_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/telemetryconfigview.kv'

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
        Logger.info("TelemetryConfig: got id:  " + value )
        if self.connectivityConfig:
            value = value.strip()
            self.ids.device_id.ids.error.text = ''
            if len(value) > 0:
                if self.validate_device_id(value):
                    kvFind(self, 'rcid', 'deviceId').setValue(value)
                    self.connectivityConfig.telemetryConfig.deviceId = value
                    self.connectivityConfig.stale = True
                    self.dispatch('on_modified')
                else:
                    self.ids.device_id.ids.error.text = 'Invalid device id. Id must only be numbers and letters.'

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
