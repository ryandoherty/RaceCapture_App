BEST_LAPTIME_KEY = 'BestLap'

class BestLapFilter(object):
    """Update BestLap if laptime is present and is faster than the current best"""
    best_laptime = 0
    best_laptime_meta = None
    def __init__(self, value, channel_metas):
        self.best_laptime_meta = channel_metas.get_meta(BEST_LAPTIME_KEY)
        
    def get_channel_meta(self):
        return self.best_laptime_meta
    
    def reset(self):
        self.best_laptime = 0
         
    def filter(self, channel_data):
        laptime = channel_data.get('LapTime')
        if laptime != None and laptime > 0:
            current_best_laptime = self.best_laptime
            if current_best_laptime == 0 or laptime < current_best_laptime: 
                current_best_laptime = laptime
                channel_data[BEST_LAPTIME_KEY] = current_best_laptime
                self.best_laptime = current_best_laptime
