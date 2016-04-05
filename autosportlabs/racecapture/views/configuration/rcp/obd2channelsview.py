import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.switch import Switch
from kivy.app import Builder
from iconbutton import IconButton
from settingsview import SettingsSwitch
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.OBD2.obd2settings import OBD2Settings
from utils import *
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.theme.color import ColorScheme
from autosportlabs.widgets.scrollcontainer import ScrollContainer

OBD2_CHANNELS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/obd2channelsview.kv'

class OBD2Channel(BoxLayout):
    channel = None
    channels = None
    obd2_settings = None
    max_sample_rate = 0
    pidIndex = 0

    def __init__(self, obd2_settings, max_sample_rate, **kwargs):
        super(OBD2Channel, self).__init__(**kwargs)
        self.obd2_settings = obd2_settings
        self.max_sample_rate = max_sample_rate
        self.register_event_type('on_delete_pid')
        self.register_event_type('on_modified')
        self.ids.chan_id.bind(on_channel = self.on_channel)

    def on_channel(self, *args):
        if self.channel:
            self.channel.stale = True
            pid = self.obd2_settings.getPidForChannelName(self.channel.name)
            self.channel.pidId = pid
            self.dispatch('on_modified')
        
    def on_modified(self):
        pass

    def on_sample_rate(self, instance, value):
        if self.channel:
            self.channel.sampleRate = instance.getValueFromKey(value)
            self.dispatch('on_modified')
                
    def on_delete_pid(self, pidId):
        pass
    
    def on_delete(self):
        self.dispatch('on_delete_pid', self.pidIndex)
        
    def set_channel(self, pidIndex, channel, channels):
        self.channel = channel
        self.pidIndex = pidIndex
        self.channels = channels
        sample_rate_spinner = self.ids.sr
        sample_rate_spinner.set_max_rate(self.max_sample_rate)        
        sample_rate_spinner.setFromValue(channel.sampleRate)
        channel_editor = self.ids.chan_id
        channel_editor.filter_list = self.obd2_settings.getChannelNames()
        channel_editor.on_channels_updated(channels)
        channel_editor.setValue(channel)
                
class OBD2ChannelsView(BaseConfigView):
    DEFAULT_OBD2_SAMPLE_RATE = 1    
    obd2_cfg = None
    max_sample_rate = 0
    obd2_grid = None
    obd2_settings = None
    base_dir = None
    
    def __init__(self, **kwargs):
        Builder.load_file(OBD2_CHANNELS_VIEW_KV)
        super(OBD2ChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.obd2_grid = self.ids.obd2grid
        obd2_enable = self.ids.obd2enable
        obd2_enable.bind(on_setting=self.on_obd2_enabled)
        obd2_enable.setControl(SettingsSwitch())
        self.base_dir = kwargs.get('base_dir')
        
        self.obd2_settings = OBD2Settings(base_dir=self.base_dir)
        
        self.update_view_enabled()

    def on_modified(self, *args):
        if self.obd2_cfg:
            self.obd2_cfg.stale = True
            self.dispatch('on_config_modified', *args)

    def on_obd2_enabled(self, instance, value):
        if self.obd2_cfg:
            self.obd2_cfg.enabled = value
            self.dispatch('on_modified')
                    
    def on_config_updated(self, rc_cfg):
        obd2_cfg = rc_cfg.obd2Config
        max_sample_rate = rc_cfg.capabilities.sample_rates.sensor
        self.ids.obd2enable.setValue(obd2_cfg.enabled)
        
        self.obd2_grid.clear_widgets()
        self.reload_obd2_channel_grid(obd2_cfg, max_sample_rate)
        self.obd2_cfg = obd2_cfg
        self.max_sample_rate = max_sample_rate
        self.update_view_enabled()

    def update_view_enabled(self):
        add_disabled = True
        if self.obd2_cfg:
            if len(self.obd2_cfg.pids) < OBD2_CONFIG_MAX_PIDS:
                add_disabled = False
                
        self.ids.addpid.disabled = add_disabled
            
    def reload_obd2_channel_grid(self, obd2_cfg, max_sample_rate):
        self.obd2_grid.clear_widgets()
        
        for i in range(len(obd2_cfg.pids)):
            pidConfig = obd2_cfg.pids[i]
            self.add_obd2_channel(i, pidConfig, max_sample_rate)
            
        self.update_view_enabled()

    def on_delete_pid(self, instance, pidIndex):
        del self.obd2_cfg.pids[pidIndex]
        self.reload_obd2_channel_grid(self.obd2_cfg, self.max_sample_rate)
        self.dispatch('on_modified')
                    
    def add_obd2_channel(self, index, pidConfig, max_sample_rate):
        channel = OBD2Channel(obd2_settings = self.obd2_settings, max_sample_rate = max_sample_rate)
        channel.bind(on_delete_pid=self.on_delete_pid)
        channel.set_channel(index, pidConfig, self.channels)
        channel.bind(on_modified=self.on_modified)
        self.obd2_grid.add_widget(channel)
        
    def on_add_obd2_channel(self):
        if (self.obd2_cfg):
            pidConfig = PidConfig()
            pidConfig.sampleRate = self.DEFAULT_OBD2_SAMPLE_RATE
            self.obd2_cfg.pids.append(pidConfig)
            self.add_obd2_channel(len(self.obd2_cfg.pids) - 1, pidConfig, self.max_sample_rate)
            self.update_view_enabled()
            self.dispatch('on_modified')        
