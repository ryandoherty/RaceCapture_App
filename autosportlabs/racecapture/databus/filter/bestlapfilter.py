

class BestLapFilter(object):
    """Update BestLap if laptime is present and is faster than the current best"""
    BEST_LAPTIME_KEY = 'BestLap'
    LAPTIME_KEY = 'LapTime'
    best_laptime = 0
    best_laptime_meta = None
    def __init__(self, system_channels):
        self.best_laptime_meta = system_channels.findChannelMeta(BestLapFilter.BEST_LAPTIME_KEY)
        
    def get_channel_meta(self, channel_meta):
        metas = {}
        if channel_meta.get(self.LAPTIME_KEY):
            metas[BestLapFilter.BEST_LAPTIME_KEY] = self.best_laptime_meta
        return metas
    
    def reset(self):
        self.best_laptime = 0
         
    def filter(self, channel_data):
        laptime = channel_data.get(self.LAPTIME_KEY)
        if laptime is not None and laptime > 0:
            current_best_laptime = self.best_laptime
            if current_best_laptime == 0 or laptime < current_best_laptime: 
                current_best_laptime = laptime
                channel_data[self.BEST_LAPTIME_KEY] = current_best_laptime
                self.best_laptime = current_best_laptime
