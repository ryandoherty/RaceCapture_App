BEST_LAPTIME_KEY = 'BestLap'

class BestLapFilter(object):
    best_laptime = 0
    best_laptime_meta = None
    def __init__(self, value, channel_metas):
        self.best_laptime_meta = channel_metas.get_meta(BEST_LAPTIME_KEY)
        
    def get_channel_meta(self):
        return self.best_laptime_meta
        
    def filter(self, channel_data):
        laptime = channel_data.get('LapTime')
        if laptime != None:
            if laptime < self.best_laptime: 
                self.best_laptime = laptime
            channel_data[BEST_LAPTIME_KEY] = self.best_laptime
