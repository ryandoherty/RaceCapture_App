import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.switch import Switch
from kivy.app import Builder
from iconbutton import IconButton
from settingsview import SettingsSwitch
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.OBD2.obd2settings import OBD2Settings
from utils import *
from autosportlabs.racecapture.config.rcpconfig import *

OBD2_CHANNELS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/obd2channelsview.kv'

class OBD2Channel(BoxLayout):
    obd2Channel = None
    channels = None
    obd2Settings = None
    pidIndex = 0

    def __init__(self, **kwargs):
        super(OBD2Channel, self).__init__(**kwargs)
        self.obd2Settings = kwargs.get('obd2Settings')
        self.register_event_type('on_delete_pid')
        self.register_event_type('on_modified')

    def on_modified(self):
        pass

    def on_channel(self, instance, value):
        if self.obd2Channel:
            self.obd2Channel.name = value
            pid = self.obd2Settings.getPidForChannelName(value)
            self.obd2Channel.pidId = pid
            self.dispatch('on_modified')            

    def on_sample_rate(self, instance, value):
        if self.obd2Channel:
            self.obd2Channel.sampleRate = instance.getValueFromKey(value)
            self.dispatch('on_modified')
                
    def on_delete_pid(self, pidId):
        pass
    
    def on_delete(self):
        self.dispatch('on_delete_pid', self.pidIndex)
        
    def set_channel(self, pidIndex, channel, channels):
        self.obd2Channel = channel
        self.pidIndex = pidIndex
        self.channels = channels
        kvFind(self, 'rcid', 'pidIndex').text = str(pidIndex + 1)
        kvFind(self, 'rcid', 'sr').setFromValue(channel.sampleRate)
        channelSpinner = kvFind(self, 'rcid', 'chanId')
        channelSpinner.filterList = self.obd2Settings.getChannelNames()
        channelSpinner.on_channels_updated(channels)
        channelSpinner.text = channel.name
        #self.dispatch('on_modified')
                
class OBD2ChannelsView(BaseConfigView):
    obd2Cfg = None
    obd2Grid = None
    obd2Settings = None
    base_dir = None
    def __init__(self, **kwargs):
        Builder.load_file(OBD2_CHANNELS_VIEW_KV)
        super(OBD2ChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.obd2Grid = kvFind(self, 'rcid', 'obd2grid')
        obd2Enable = kvFind(self, 'rcid', 'obd2enable')
        obd2Enable.bind(on_setting=self.on_obd2_enabled)
        obd2Enable.setControl(SettingsSwitch())
        self.base_dir = kwargs.get('base_dir')
        
        self.obd2Settings = OBD2Settings(base_dir=self.base_dir)
        
        self.update_view_enabled()

    def on_modified(self, *args):
        if self.obd2Cfg:
            self.obd2Cfg.stale = True
            self.dispatch('on_config_modified', *args)

    def on_obd2_enabled(self, instance, value):
        if self.obd2Cfg:
            self.obd2Cfg.enabled = value
            self.dispatch('on_modified')
                    
    def on_config_updated(self, rcpCfg):
        obd2Cfg = rcpCfg.obd2Config
        
        kvFind(self, 'rcid', 'obd2enable').setValue(obd2Cfg.enabled)
        
        self.obd2Grid.clear_widgets()
        self.reload_obd2_channel_grid(obd2Cfg)
        self.obd2Cfg = obd2Cfg
        self.update_view_enabled()

    def update_view_enabled(self):
        add_disabled = True
        if self.obd2Cfg:
            if len(self.obd2Cfg.pids) < OBD2_CONFIG_MAX_PIDS:
                add_disabled = False
                
        kvFind(self, 'rcid', 'addpid').disabled = add_disabled
            
    def reload_obd2_channel_grid(self, obd2Cfg):
        self.obd2Grid.clear_widgets()
        
        for i in range(len(obd2Cfg.pids)):
            pidConfig = obd2Cfg.pids[i]
            self.add_obd2_channel(i, pidConfig)
            
        self.update_view_enabled()

    def on_delete_pid(self, instance, pidIndex):
        del self.obd2Cfg.pids[pidIndex]
        self.reload_obd2_channel_grid(self.obd2Cfg)
        self.dispatch('on_modified')
                    
    def add_obd2_channel(self, index, pidConfig):
        obd2Channel = OBD2Channel(obd2Settings = self.obd2Settings)
        obd2Channel.bind(on_delete_pid=self.on_delete_pid)
        obd2Channel.set_channel(index, pidConfig, self.channels)
        obd2Channel.bind(on_modified=self.on_modified)
        self.obd2Grid.add_widget(obd2Channel)
        
    def on_add_obd2_channel(self):
        if (self.obd2Cfg):
            pidConfig = PidConfig()
            self.obd2Cfg.pids.append(pidConfig)
            self.add_obd2_channel(len(self.obd2Cfg.pids) - 1, pidConfig)
            self.update_view_enabled()
            self.dispatch('on_modified')        
