import kivy
kivy.require('1.9.1')

from settingsview import SettingsMappedSpinner, SettingsSwitch
from mappedspinner import MappedSpinner
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from utils import *
from settingsview import SettingsView
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView

CAN_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/canconfigview.kv'

class CANBaudRateSettings(SettingsView):
    channel_id = 0

class CANBaudRateSpinner(SettingsMappedSpinner):
    def __init__(self, **kwargs):    
        super(CANBaudRateSpinner, self).__init__(**kwargs)
        self.setValueMap({50000: '50K Baud', 100000: '100K Baud', 125000: '125K Baud', 250000:'250K Baud', 500000:'500K Baud', 1000000:'1M Baud'}, 500000)
    
class CANConfigView(BaseConfigView):
    can_config = None
    can_settings = []
    
    def __init__(self, **kwargs):    
        Builder.load_file(CAN_CONFIG_VIEW_KV)
        super(CANConfigView, self).__init__(**kwargs)
        
        self.register_event_type('on_config_updated')    
        btEnable = self.ids.can_enabled 
        btEnable.bind(on_setting=self.on_can_enabled)
        btEnable.setControl(SettingsSwitch())
                
    def on_can_enabled(self, instance, value):
        if self.can_config:
            self.can_config.enabled = value
            self.can_config.stale = True
            self.dispatch('on_modified')            
    
    def on_can_baud(self, instance, value):
        if self.can_config:
            channel_id = instance.channel_id
            self.can_config.baudRate[channel_id] = value
            self.can_config.stale = True
            self.dispatch('on_modified')
    
    def on_config_updated(self, rcpCfg):
        can_config = rcpCfg.canConfig
        self.ids.can_enabled.setValue(can_config.enabled)
        self.update_can_baud_rates(rcpCfg)
        self.can_config = can_config
        
    def update_can_baud_rates(self, rcpCfg):
        can_config = rcpCfg.canConfig
        capabilities = rcpCfg.capabilities
        can_baud_container = self.ids.can_bauds
        current_children = can_baud_container.children
        can_channel_count = capabilities.channels.can
        if len(current_children) != can_channel_count:
            self.can_settings = []
            can_baud_container.clear_widgets
            for i in range(0, can_channel_count):
                can_baud_rate_setting = CANBaudRateSettings()
                self.can_settings.append(can_baud_rate_setting)
                can_baud_rate_setting.channel_id = i
                can_baud_rate_setting.label_text = 'CAN {} Baud Rate'.format(i + 1)
                can_baud_rate_setting.setControl(CANBaudRateSpinner())
                can_baud_rate_setting.bind(on_setting=self.on_can_baud)        
                can_baud_container.add_widget(can_baud_rate_setting)
                
        for settings, baud in zip(self.can_settings, can_config.baudRate):
            settings.setValue(baud)                
            

