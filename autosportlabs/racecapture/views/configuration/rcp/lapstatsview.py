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
    
    def __init__(self, **kwargs):
        Builder.load_file(LAPSTATS_VIEW_KV)            
        super(LapStatsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')

    
    def setLapStatChannel(self, channel, spinner):
        channel.sampleRate = spinner.getSelectedValue()
        self.lapConfig.stale = True
        self.dispatch('on_modified')
        
    def on_lapCount_sample_rate(self, instance, value):
        if self.lapConfig:
            self.setLapStatChannel(self.lapConfig.lapCount, instance)
            
    def on_lapTime_sample_rate(self, instance, value):
        if self.lapConfig:
            self.setLapStatChannel(self.lapConfig.lapTime, instance)
            
    def on_predTime_sample_rate(self, instance, value):
        if self.lapConfig:
            self.setLapStatChannel(self.lapConfig.predTime, instance)
        
    def on_sector_sample_rate(self, instance, value):
        if self.lapConfig:
            self.setLapStatChannel(self.lapConfig.sector, instance)
        
    def on_sectorTime_sample_rate(self, instance, value):
        if self.lapConfig:
            self.setLapStatChannel(self.lapConfig.sectorTime, instance)
        
    def setSampleRateSpinner(self, rcid, sampleRate):
        kvFind(self, 'rcid', rcid).setFromValue(sampleRate)
        
    def on_config_updated(self, rcpCfg):
        lapConfig = rcpCfg.lapConfig
        
        self.setSampleRateSpinner('lapCount', lapConfig.lapCount.sampleRate)
        self.setSampleRateSpinner('lapTime', lapConfig.lapTime.sampleRate)
        self.setSampleRateSpinner('predTime', lapConfig.predTime.sampleRate)
        self.setSampleRateSpinner('sector', lapConfig.sector.sampleRate)                
        self.setSampleRateSpinner('sectorTime', lapConfig.sectorTime.sampleRate)
        self.lapConfig = lapConfig        
        