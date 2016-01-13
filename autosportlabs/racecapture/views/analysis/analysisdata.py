from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from threading import Thread
from kivy.logger import Logger
import Queue

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
        
class ChannelDataParams(object):
    def __init__(self, get_function, source_ref, channels, callback):
        self.get_function = get_function
        self.source_ref = source_ref
        self.channels = channels
        self.callback = callback

class LocationDataParams(object):
    def __init__(self, get_function, source_ref, callback):
        self.get_function = get_function
        self.source_ref = source_ref
        self.callback = callback
        
class CachingAnalysisDatastore(DataStore):
    
    def __init__(self, **kwargs):
        super(CachingAnalysisDatastore, self).__init__(**kwargs)
        self.query_queue= Queue.Queue()
        self._channel_data_cache = {}
        self._session_location_cache = {}        
        
        #Worker thread for querying data
        t = Thread(target=self._get_channel_data_worker)
        t.daemon = True
        t.start()


    def _query_channel_data(self, source_ref, channel):
        Logger.info('CachingAnalysisDatastore: querying ' + str(source_ref) + ' ' +  channel)
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
                
    def _get_channel_data(self, params):
        source_key = str(params.source_ref)
        channel_data = self._channel_data_cache.get(source_key)
        if not channel_data:
            channel_data = {}
            self._channel_data_cache[source_key] = channel_data
        
        for channel in params.channels:
            channel_d = channel_data.get(channel)
            if not channel_d:
                channel_d = self._query_channel_data(params.source_ref, channel)
                channel_data[channel] = channel_d
        params.callback(channel_data)

    def _get_location_data(self, params):
        source_ref = params.source_ref
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
        params.callback(cache)
        
    def _get_channel_data_worker(self):
        '''
        Worker to fetch requested data and perform queries as necessary
        '''
        while True:
            item = self.query_queue.get()
            item.get_function(item)
            self.query_queue.task_done()

    def get_channel_data(self, source_ref, channels, callback):
        self.query_queue.put(ChannelDataParams(self._get_channel_data, source_ref, channels, callback))
        
    def get_location_data(self, source_ref, callback):
        self.query_queue.put(LocationDataParams(self._get_location_data, source_ref, callback))
        
    def get_cached_location_data(self, source_ref):
        return self._session_location_cache.get(str(source_ref))
        
        
        
