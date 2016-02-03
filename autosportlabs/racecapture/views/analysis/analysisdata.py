#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
#have received a copy of the GNU General Public License along with
#this code. If not, see <http://www.gnu.org/licenses/>.
from autosportlabs.racecapture.datastore import DataStore, Filter, timing
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
    '''
    Parameters for querying channel data
    '''
    def __init__(self, get_function, source_ref, channels, callback):
        self.get_function = get_function
        self.source_ref = source_ref
        self.channels = channels
        self.callback = callback

class LocationDataParams(object):
    '''
    Parameters for querying location data
    '''
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


    @timing
    def _query_channel_data(self, source_ref, channels, combined_channel_data):
        Logger.info('CachingAnalysisDatastore: querying {} {}'.format(source_ref, channels))
        lap = source_ref.lap
        session = source_ref.session
        f = Filter().eq('LapCount', lap)
        dataset = self.query(sessions=[session], channels=channels, data_filter=f)
        records = dataset.fetch_records()

        for index in range(len(channels)):
            channel = channels[index]
            values = []
            for record in records:
                #pluck out just the channel value
                values.append(record[1 + index])

            channel_meta = self.get_channel(channel)
            channel_data = ChannelData(values=values, channel=channel, min=channel_meta.min, max=channel_meta.max, source=source_ref)
            combined_channel_data[channel] = channel_data
                
    def _get_channel_data(self, params):
        '''
        Retrieve cached or query channel data as appropriate.
        '''
        source_key = str(params.source_ref)
        channel_data = self._channel_data_cache.get(source_key)
        if not channel_data:
            channel_data = {}
            self._channel_data_cache[source_key] = channel_data
        
        channels_to_query = []
        for channel in params.channels:
            channel_d = channel_data.get(channel)
            if not channel_d:
                channels_to_query.append(channel)

        if len(channels_to_query) > 0:
            channel_d = self._query_channel_data(params.source_ref, channels_to_query, channel_data)

        params.callback(channel_data)

    def _get_location_data(self, params):
        '''
        Retrieve cached or query Location data as appropriate.
        '''
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
        Worker to fetch requested data and perform queries as necessary. Work is queued
        so multiple requests prevent a race condition or trigger multiple queries for the same data.
        '''
        while True:
            item = self.query_queue.get()
            item.get_function(item)
            self.query_queue.task_done()

    def get_channel_data(self, source_ref, channels, callback):
        '''
        Retrieve channel data for the specified source (session / lap combo).
        Data is returned with the specified callback function.
        '''
        self.query_queue.put(ChannelDataParams(self._get_channel_data, source_ref, channels, callback))
        
    def get_location_data(self, source_ref, callback=None):
        '''
        Retrieve location data for the specified source (session / lap combo). 
        If immediately available, return it, otherwise use the callback for a later return after querying.
        '''
        cached = self._session_location_cache.get(str(source_ref))
        if callback:
            if cached:
                callback(cached)
            else:
                self.query_queue.put(LocationDataParams(self._get_location_data, source_ref, callback))
        return cached

        
        
