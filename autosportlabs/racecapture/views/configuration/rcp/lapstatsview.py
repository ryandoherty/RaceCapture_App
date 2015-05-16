import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from samplerateview import *
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *

LAPSTATS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/lapstatsview.kv'

class LapStatsView(BaseConfigView):
    lapConfig = None
    gps_config = None
    
    def __init__(self, **kwargs):
        Builder.load_file(LAPSTATS_VIEW_KV)            
        super(LapStatsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.ids.lapstats.bind(on_setting=self.on_lapstats_enabled)
        self.ids.predtime.bind(on_setting=self.on_predtime_enabled)
        
    def on_lapstats_enabled(self, instance, value):
        lap_cfg = self.lapConfig
        self._normalize_lap_config(lap_cfg, self.gps_config, value)
        lap_cfg.stale = True
        self.dispatch('on_modified')
        
    def on_predtime_enabled(self, instance, value):
        if value: #force lapstats enabled if we enable prdictive timing
            self.ids.lapstats.setValue(True)
        rate = LapConfig.DEFAULT_PREDICTED_TIME_SAMPLE_RATE if value else 0
        config = self.lapConfig
        config.predTime.sampleRate = rate
        config.stale = True
        self.dispatch('on_modified')
    
    def _any_lapstats_enabled(self, lap_config):
        return (lap_config.lapCount.sampleRate > 0 or 
            lap_config.lapTime.sampleRate > 0 or 
            lap_config.sector.sampleRate > 0 or 
            lap_config.sectorTime.sampleRate > 0 or 
            lap_config.elapsedTime.sampleRate > 0 or 
            lap_config.currentLap.sampleRate > 0)
        
    def _normalize_lap_config(self, lap_cfg, gps_cfg, lapstats_enabled):
        gps_sample_rate = gps_cfg.sampleRate
        rate = gps_sample_rate if lapstats_enabled else 0
        lap_cfg.lapTime.sampleRate = rate
        lap_cfg.sector.sampleRate = rate
        lap_cfg.sectorTime.sampleRate = rate
        lap_cfg.elapsedTime.sampleRate = rate
        lap_cfg.currentLap.sampleRate = rate
            
    def on_config_updated(self, rcp_cfg):
        lapConfig = rcp_cfg.lapConfig
        
        any_lapstats_enabled = self._any_lapstats_enabled(lapConfig)
        self._normalize_lap_config(lapConfig, rcp_cfg.gpsConfig, any_lapstats_enabled)
        self.ids.lapstats.setValue(any_lapstats_enabled)
        
        if lapConfig.predTime.sampleRate > 0:
            self.ids.predtime.sampleRate.setValue(True)
            
        self.lapConfig = lapConfig
        self.gps_config = rcp_cfg.gpsConfig     
        