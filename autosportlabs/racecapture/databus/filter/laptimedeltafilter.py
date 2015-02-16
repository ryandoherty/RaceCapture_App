LAPTIME_KEY         = 'LapTime'
PREDTIME_KEY        = 'PredTime'
BEST_LAPTIME_KEY    = 'BestLap'
LAP_DELTA_KEY       = 'LapDelta'

class DeltaTimeFilter(object):
    """Update the DeltaTime if BestLap and a reference lap time is available. 
    The Reference Lap is based on the current predicted lap time, or if not available, the 
    last lap time.
    
    A negative delta value means we are ahead of the last best lap
    """    
    lap_delta_meta = None
    def __init__(self, value, channel_metas):
        self.lap_delta_meta = channel_metas.get_meta(LAP_DELTA_KEY)
        
    def reset(self):
        pass
    
    def get_channel_meta(self):
        return self.best_laptime_meta
        
    def filter(self, channel_data):
        laptime = channel_data.get(LAPTIME_KEY)
        predtime = channel_data.get(PREDTIME_KEY)
        best_laptime = channel_data.get(BEST_LAPTIME_KEY)
        
        #we choose predicted laptime if it is present in the data stream
        reference_laptime = laptime if predtime == None else predtime
        delta_time = 0.0
        if reference_laptime and best_laptime:
            delta_time = reference_laptime - best_laptime
        channel_data[LAP_DELTA_KEY] = delta_time
