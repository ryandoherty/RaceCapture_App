from autosportlabs.racecapture.views.analysis.analysiswidget import ChannelAnalysisWidget, ChannelData
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent
from autosportlabs.uix.color.colorsequence import ColorSequence
from autosportlabs.racecapture.datastore import Filter

from installfix_garden_graph import Graph, LinePlot, SmoothLinePlot
from kivy.app import Builder
from kivy.core.window import Window
Builder.load_file('autosportlabs/racecapture/views/analysis/linechart.kv')

class ChannelPlot(object):
    plot = None
    channel = None
    min_value = 0
    max_value = 0
    lap = None
    sourceref = None
    distance_index = {}
    samples = 0
    def __init__(self, plot, channel, min_value, max_value, sourceref):
        self.plot = plot
        self.channel = channel
        self.min_value = min_value
        self.max_value = max_value
        self.sourceref = sourceref
        
    def __str__(self):
        return "{}_{}".format(str(self.sourceref), self.channel) 
    
class LineChart(ChannelAnalysisWidget):
    _channel_plots = {}
    _color_sequence = ColorSequence()
    
    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.register_event_type('on_marker')
    
    def on_marker(self, marker_event):
        pass

    def remove_channel(self, channel, ref):
        remove = []
        for channel_plot in self._channel_plots.itervalues():
            if channel_plot.channel == channel and str(ref) == str(channel_plot.sourceref):
                remove.append(channel_plot)
        
        for channel_plot in remove:
            self.ids.chart.remove_plot(channel_plot.plot)
            del(self._channel_plots[str(channel_plot)])

    
    def add_channel(self, channel_data):
        chart = self.ids.chart
        plot = SmoothLinePlot(color=self._color_sequence.get_next_color())
        channel_plot = ChannelPlot(plot, 
                                   channel_data.channel, 
                                   channel_data.min, 
                                   channel_data.max, 
                                   channel_data.source)
        chart.add_plot(plot)
        points = []
        distance_index = {}
        max_distance = chart.xmax
        sample_index = 0
        for sample in channel_data.data:
            distance = sample[1]
            if distance > max_distance:
                max_distance = distance 
            points.append((distance, sample[2]))
            distance_index[distance] = sample_index
            sample_index += 1
        
        channel_plot.distance_index = distance_index
        channel_plot.samples = sample_index            
        chart.ymin = channel_data.min
        chart.ymax = channel_data.max
        chart.xmin = 0
        chart.xmax = max_distance
        plot.points = points
        self._channel_plots[str(channel_plot)] = channel_plot
    
    def query_new_channel(self, channel, lap_ref):
        lap = lap_ref.lap
        session = lap_ref.session
        f = Filter().eq('LapCount', lap)
        dataset = self.datastore.query(sessions=[session],
                         channels=['Distance', channel], data_filter=f)

        channel_meta = self.datastore.get_channel(channel)
        records = dataset.fetch_records()
        channel_data = ChannelData(data=records, channel=channel, min=channel_meta.min, max=channel_meta.max, source=lap_ref)
        self.add_channel(channel_data)

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            if hasattr(touch, 'button'):
                button = touch.button
                scroll_dir = 0
                if touch.is_mouse_scrolling:
                    if 'down' in button or 'left' in button:
                        scroll_dir = 1
                    if 'up' in button or 'right' in button:
                        scroll_dir = -1
        super(LineChart, self).on_touch_down(touch)
        return False
        
        
    def dispatch_marker(self, x, y):
        mouse_x = x - self.pos[0]
        width = self.size[0]
        pct = mouse_x / width
        
        for channel_plot in self._channel_plots.itervalues():
            data_index = int(channel_plot.samples * pct)
            marker = MarkerEvent(data_index, channel_plot.sourceref)
            self.dispatch('on_marker', marker)
        
    def on_touch_move(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        self.dispatch_marker(touch.x, touch.y)
        
    def on_mouse_pos(self, x, pos):
        if not self.collide_point(pos[0], pos[1]):
            return False
        
        self.dispatch_marker(pos[0], pos[1])
