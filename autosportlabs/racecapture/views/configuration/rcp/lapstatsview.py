import traceback
import kivy
kivy.require('1.9.1')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from samplerateview import *
from utils import *
from settingsview import SettingsSwitch
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *

LAPSTATS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/lapstatsview.kv'

class LapStatsView(BaseConfigView):
    lap_config = None
    gps_config = None
    
    def __init__(self, **kwargs):
        Builder.load_file(LAPSTATS_VIEW_KV)            
        super(LapStatsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.ids.lapstats.setControl(SettingsSwitch())
        self.ids.lapstats.bind(on_setting=self.on_lapstats_enabled)
        self.ids.predtime.setControl(SettingsSwitch())
        self.ids.predtime.bind(on_setting=self.on_predtime_enabled)
        
    def on_lapstats_enabled(self, instance, value):
        if self.lap_config:
            lap_cfg = self.lap_config
            self._normalize_lap_config(lap_cfg, self.gps_config, value)
            lap_cfg.stale = True
            self.dispatch('on_modified')
            if not value:
                self.ids.predtime.setValue(False)
        
    def on_predtime_enabled(self, instance, value):
        if self.lap_config:
            if value: #force lapstats enabled if we enable prdictive timing
                self.ids.lapstats.setValue(True)
            rate = LapConfig.DEFAULT_PREDICTED_TIME_SAMPLE_RATE if value else 0
            config = self.lap_config
            config.predTime.sampleRate = rate
            config.stale = True
            self.dispatch('on_modified')
    
    def _normalize_lap_config(self, lap_cfg, gps_cfg, lapstats_enabled):
        gps_sample_rate = gps_cfg.sampleRate
        rate = gps_sample_rate if lapstats_enabled else 0
        lap_cfg.set_primary_stats(rate)
            
    def on_config_updated(self, rcp_cfg):
        lap_config = rcp_cfg.lapConfig
        gps_config = rcp_cfg.gpsConfig
        
        primary_stats_enabled = lap_config.primary_stats_enabled()
        self._normalize_lap_config(lap_config, gps_config, primary_stats_enabled)
        self.ids.lapstats.setValue(primary_stats_enabled)
        
        if lap_config.predTime.sampleRate > 0:
            self.ids.predtime.setValue(True)
            
        self.gps_config = rcp_cfg.gpsConfig
        self.lap_config = lap_config
                 
        