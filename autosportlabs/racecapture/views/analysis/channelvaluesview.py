import kivy
kivy.require('1.9.0')
from kivy.logger import Logger
from kivy.app import Builder
from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from autosportlabs.racecapture.views.analysis.analysiswidget import ChannelAnalysisWidget, ChannelData
Builder.load_file('autosportlabs/racecapture/views/analysis/channelvaluesview.kv')

class ChannelStats(object):
    def __init__(self, **kwargs):
        self.values = kwargs.get('values')
        self.min = kwargs.get('min')
        self.max = kwargs.get('max')
        self.avg = kwargs.get('avg')
    
class ChannelValuesView(ChannelAnalysisWidget):
    
    def __init__(self, **kwargs):
        super(ChannelValuesView, self).__init__(**kwargs)
        self.channel_stats={}

    def update_reference_mark(self, source, point):
        channel_data = self.channel_stats.get(str(source))
        for channel, channel_data in channel_data.iteritems():
            stats = channel_data.data
            print(str(source) + ' ' + channel + ': ' + str(stats.values[point]) + ': ' + str(stats.min) + ' ' + str(stats.max) + ' ' + str(stats.avg))

    def add_channel(self, channel_data):
        source_key = str(channel_data.source)
        channels = self.channel_stats.get(source_key)
        if not channels:
            channels = {}
            self.channel_stats[source_key] = channels
        channels[channel_data.channel] = channel_data
    
    def remove_channel(self, channel, ref):
        print('remove channel ' + str(channel))
        
    def query_new_channel(self, channel, lap_ref):
        lap = lap_ref.lap
        session = lap_ref.session
        f = Filter().eq('LapCount', lap)
        dataset = self.datastore.query(sessions=[session], channels=[channel], data_filter=f)
        
        channel_meta = self.datastore.get_channel(channel)
        records = dataset.fetch_records()
        channel_min = self.datastore.get_channel_min(channel)
        channel_max = self.datastore.get_channel_max(channel)
        channel_avg = self.datastore.get_channel_average(channel)
        
        values = []
        for record in records:
            #pluck out just the channel value
            values.append(record[1])
            
        stats = ChannelStats(values=values, min=channel_min, max=channel_max, avg=channel_avg)
        channel_data = ChannelData(data=stats, channel=channel, min=channel_meta.min, max=channel_meta.max, source=lap_ref)
        self.add_channel(channel_data)
                
                