import kivy
kivy.require('1.9.1')

from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.app import Builder
from fieldlabel import FieldLabel
from valuefield import IntegerValueField
from mappedspinner import MappedSpinner
from utils import *
from kivy.metrics import dp
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseMultiChannelConfigView, BaseChannelView

ANALOG_PULSE_CHANNELS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/pwmchannelsview.kv'

class AnalogPulseOutputChannelsView(BaseMultiChannelConfigView):
    def __init__(self, **kwargs):
        Builder.load_file(ANALOG_PULSE_CHANNELS_VIEW_KV)
        super(AnalogPulseOutputChannelsView, self).__init__(**kwargs)
        self.channel_title = 'Pulse / Analog Output '
        self.accordion_item_height = dp(100)
        
    def channel_builder(self, index, max_sample_rate):
        editor = AnalogPulseOutputChannel(id='pwm' + str(index), channels=self.channels)
        editor.bind(on_modified=self.on_modified)
        if self.config:
            editor.on_config_updated(self.config.channels[index], max_sample_rate)
        return editor
            
    def get_specific_config(self, rcp_cfg):
        return rcp_cfg.pwmConfig

    
class PwmOutputModeSpinner(MappedSpinner):
    def __init__(self, **kwargs):
        super(PwmOutputModeSpinner, self).__init__(**kwargs)
        self.setValueMap({0:'Analog', 1:'Frequency'}, 'Frequency')

class PwmLoggingModeSpinner(MappedSpinner):
    def __init__(self, **kwargs):
        super(PwmLoggingModeSpinner, self).__init__(**kwargs)
        self.setValueMap({0:'Period', 1:'Duty Cycle', 2:'Volts'}, 'Duty Cycle')
    
class AnalogPulseOutputChannel(BaseChannelView):
    def __init__(self, **kwargs):
        super(AnalogPulseOutputChannel, self).__init__(**kwargs)
                        
    def on_output_mode(self, instance, value):
        if self.channelConfig:
            self.channelConfig.outputMode = instance.getValueFromKey(value)
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                        
    def on_logging_mode(self, instance, value):
        if self.channelConfig:
            self.channelConfig.loggingMode = instance.getValueFromKey(value)
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                            
    def on_startup_duty_cycle(self, instance, value):
        if self.channelConfig:
            self.channelConfig.startupDutyCycle = int(value)
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                            
    def on_startup_period(self, instance, value):
        if self.channelConfig:
            self.channelConfig.startupPeriod = int(value)
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                            
    def on_voltage_scaling(self, instance, value):
        if self.channelConfig:
            self.channelConfig.voltageScaling = float(value)
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                        
    def on_config_updated(self, channelConfig, max_sample_rate):
        self.ids.chan_id.setValue(channelConfig)
        self.ids.sr.setValue(channelConfig.sampleRate, max_sample_rate)
                
        startupDutyCycle = kvFind(self, 'rcid', 'dutyCycle')
        startupDutyCycle.text = str(channelConfig.startupDutyCycle)
        
        startupPeriod = kvFind(self, 'rcid', 'period')
        startupPeriod.text = str(channelConfig.startupPeriod)
        
        outputModeSpinner = kvFind(self, 'rcid', 'outputMode')
        outputModeSpinner.setFromValue(channelConfig.outputMode)
        
        loggingModeSpinner = kvFind(self, 'rcid', 'loggingMode')
        loggingModeSpinner.setFromValue(channelConfig.loggingMode)
        
        self.channelConfig = channelConfig
        
