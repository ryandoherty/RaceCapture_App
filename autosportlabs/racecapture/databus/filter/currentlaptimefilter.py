

class CurrentLapTimeFilter(object):
    """Prefer PredTime over LapTime for setting CurLapTime channel"""
    PREDICTED_LAPTIME_KEY = 'PredTime'
    LAST_LAPTIME_KEY = 'LapTime'
    CURRENT_LAPTIME_KEY = 'CurLapTime'
    current_laptime_meta = None
    
    def __init__(self, system_channels):
        self.current_laptime_meta = system_channels.findChannelMeta(CurrentLapTimeFilter.CURRENT_LAPTIME_KEY)
        
    def get_channel_meta(self):
        return {CurrentLapTimeFilter.CURRENT_LAPTIME_KEY: self.current_laptime_meta}
    
    def reset(self):
        pass
         
    def filter(self, channel_data):
        lapTime = channel_data.get(self.LAST_LAPTIME_KEY)
        predTime = channel_data.get(self.PREDICTED_LAPTIME_KEY)
        if predTime is not None:
            channel_data[self.CURRENT_LAPTIME_KEY] = predTime
        else:
            if lapTime is not None:
                channel_data[self.CURRENT_LAPTIME_KEY] = lapTime
