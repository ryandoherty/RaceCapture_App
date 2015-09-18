import kivy
kivy.require('1.9.0')
from kivy.logger import Logger
from kivy.graphics import Color
from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from autosportlabs.racecapture.views.analysis.analysiswidget import ChannelAnalysisWidget, ChannelData
from autosportlabs.racecapture.views.analysis.bargraphgauge import BarGraphGauge

Builder.load_file('autosportlabs/racecapture/views/analysis/channelvaluesview.kv')

class ChannelStats(object):
    def __init__(self, **kwargs):
        self.values = kwargs.get('values')
        self.min = kwargs.get('min')
        self.max = kwargs.get('max')
        self.avg = kwargs.get('avg')
    
class ChannelValueView(BoxLayout):

    def __init__(self, **kwargs):
        super(ChannelValueView, self).__init__(**kwargs)
        self.session_view = self.ids.session
        self.lap_view = self.ids.lap
        self.channel_view = self.ids.channel
        self.value_view = self.ids.value

    @property
    def session(self):
        return self.session_view.text

    @session.setter
    def session(self, value):
        self.session_view.text = str(value)

    @property
    def lap(self):
        return self.lap_view.text

    @lap.setter
    def lap(self, value):
        self.lap_view.text = str(value)

    @property
    def channel(self):
        return self.channel_view.text

    @channel.setter
    def channel(self, value):
        self.channel_view.text = value

    @property
    def value(self):
        return self.value_view.value

    @value.setter
    def value(self, value):
        self.value_view.value = float(value)

    @property
    def color(self):
        return self.value_view.color

    @color.setter
    def color(self, value):
        self.value_view.color = [value[0], value[1], value[2], 0.5]

class ChannelValuesView(ChannelAnalysisWidget):
    color_sequence = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ChannelValuesView, self).__init__(**kwargs)
        self.channel_stats={}
        self._channel_stat_widgets = {}

    def update_reference_mark(self, source, point):
        channel_data = self.channel_stats.get(str(source))
        for channel, channel_data in channel_data.iteritems():
            stats = channel_data.data
            key = channel + str(source)
            widget = self._channel_stat_widgets.get(key)
            widget.session = str(source.session)
            widget.lap = str(source.lap)
            widget.channel = channel
            widget.value = str(stats.values[point])

    def _refresh_channels(self):
        channels_grid = self.ids.channel_values
        self._channel_stat_widgets.clear()
        for source_key, channels in self.channel_stats.iteritems():
            for channel, channel_data in channels.iteritems():
                key = channel + source_key
                view = ChannelValueView()
                view.channel = channel
                view.color = self.color_sequence.get_color(key)
                view.lap = channel_data.source.lap
                view.session = channel_data.source.session
                self._channel_stat_widgets[key] = view
                
        channels_grid.clear_widgets()
        for key in iter(sorted(self._channel_stat_widgets.iterkeys())):
            channels_grid.add_widget(self._channel_stat_widgets[key])
            

    def add_channel(self, channel_data):
        source_key = str(channel_data.source)
        channels = self.channel_stats.get(source_key)
        if not channels:
            channels = {}
            self.channel_stats[source_key] = channels
        channels[channel_data.channel] = channel_data
        self._refresh_channels()
    
    def refresh_view(self):
        self._refresh_channels()
        
    def remove_channel(self, channel, lap_ref):
        source_key = str(lap_ref)
        channels = self.channel_stats.get(source_key)
        channels.pop(channel, None)

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
                
                