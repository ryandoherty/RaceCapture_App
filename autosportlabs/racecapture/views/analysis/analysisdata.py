from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.geo.geopoint import GeoPoint
import threading

class ChannelStats(object):
    def __init__(self, **kwargs):
        self.values = kwargs.get('values')
        self.min = kwargs.get('min')
        self.max = kwargs.get('max')
        self.avg = kwargs.get('avg')

class ChannelData(object):
    values = None
    channel = None
    min = 0
    max = 0
    source = None
    
    def __init__(self, **kwargs):
        self.values = kwargs.get('values', None)
        self.channel = kwargs.get('channel', None)
        self.min = kwargs.get('min', 0)
        self.max = kwargs.get('max', 0)
        self.source = kwargs.get('source', None)
        
class CachingAnalysisDatastore(DataStore):
    
    def __init__(self, **kwargs):
        self._channel_data_cache = {}
        self._session_location_cache = {}        
        super(CachingAnalysisDatastore, self).__init__(**kwargs)

    def _query_channel_data(self, source_ref, channel):
        lap = source_ref.lap
        session = source_ref.session
        f = Filter().eq('LapCount', lap)
        dataset = self.query(sessions=[session], channels=[channel], data_filter=f)
        
        channel_meta = self.get_channel(channel)
        records = dataset.fetch_records()
        
        values = []
        for record in records:
            #pluck out just the channel value
            values.append(record[1])
            
        channel_data = ChannelData(values=values, channel=channel, min=channel_meta.min, max=channel_meta.max, source=source_ref)
        return channel_data
                
    def _get_channel_data_worker(self, source_ref, channels, callback):
        source_key = str(source_ref)
        channel_data = self._channel_data_cache.get(source_key)
        if not channel_data:
            channel_data = {}
            self._channel_data_cache[source_key] = channel_data
        
        for channel in channels:
            channel_d = channel_data.get(channel)
            if not channel_d:
                channel_d = self._query_channel_data(source_ref, channel)
                channel_data[channel] = channel_d
        callback(channel_data)

    def get_channel_data(self, source_ref, channels, callback):
        t = threading.Thread(target=self._get_channel_data_worker, args=(source_ref, channels, callback))
        t.start()
        
    def get_location_data(self, source_ref):
        source_key = str(source_ref)
        cache = self._session_location_cache.get(source_key)
        if cache == None:
            session = source_ref.session
            lap = source_ref.lap
            f = Filter().neq('Latitude', 0).and_().neq('Longitude', 0).eq("LapCount", lap)
            dataset = self.query(sessions = [session], 
                                            channels = ["Latitude", "Longitude"], 
                                            data_filter = f)
            records = dataset.fetch_records()
            cache = []
            for r in records:
                lat = r[1]
                lon = r[2]
                cache.append(GeoPoint.fromPoint(lat, lon))
            self._session_location_cache[source_key]=cache
        return cache
        
        
