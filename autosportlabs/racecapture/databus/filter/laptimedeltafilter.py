
class LaptimeDeltaFilter(object):
    """Update the DeltaTime if BestLap and a reference lap time is available.
    DeltaTime is in seconds: positive value means you are slower than fast lap 
    The Reference Lap is based on the current predicted lap time, or if not available, the 
    last lap time.
    
    A negative delta value means we are ahead of the last best lap
    """    
    LAPTIME_KEY         = 'LapTime'
    PREDTIME_KEY        = 'PredTime'
    BEST_LAPTIME_KEY    = 'BestLap'
    LAP_DELTA_KEY       = 'LapDelta'
    lap_delta_meta = None
    
    def __init__(self, system_channels):
        self.lap_delta_meta = system_channels.findChannelMeta(LaptimeDeltaFilter.LAP_DELTA_KEY)
        
    def reset(self):
        pass
    
    def get_channel_meta(self, channel_meta):
        metas = {}
        if channel_meta.get(self.LAPTIME_KEY):
            metas[LaptimeDeltaFilter.LAP_DELTA_KEY] = self.lap_delta_meta
        return metas
        
    def filter(self, channel_data):
        laptime = channel_data.get(LaptimeDeltaFilter.LAPTIME_KEY)
        predtime = channel_data.get(LaptimeDeltaFilter.PREDTIME_KEY)
        best_laptime = channel_data.get(LaptimeDeltaFilter.BEST_LAPTIME_KEY)
        
        #we choose predicted laptime if it is present in the data stream
        reference_laptime = laptime if predtime == None else predtime
        delta_time = 0.0
        if reference_laptime and best_laptime:
            delta_time = (reference_laptime - best_laptime) * 60.0
        channel_data[LaptimeDeltaFilter.LAP_DELTA_KEY] = delta_time
