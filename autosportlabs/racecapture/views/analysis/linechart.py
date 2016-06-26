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
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

from installfix_garden_graph import Graph, LinePlot, SmoothLinePlot
from iconbutton import IconButton, LabelIconButton
from kivy.app import Builder
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from collections import OrderedDict
from  kivy.metrics import MetricsBase
from kivy.logger import Logger
import bisect

from autosportlabs.racecapture.views.analysis.analysiswidget import ChannelAnalysisWidget
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent
from autosportlabs.uix.color.colorsequence import ColorSequence
from autosportlabs.racecapture.datastore import Filter
from autosportlabs.racecapture.views.analysis.analysisdata import ChannelData
from autosportlabs.uix.progressspinner import ProgressSpinner
from autosportlabs.uix.options.optionsview import OptionsView, BaseOptionsScreen
from autosportlabs.racecapture.views.analysis.customizechannelsview import CustomizeChannelsView

Builder.load_file('autosportlabs/racecapture/views/analysis/linechart.kv')

class ChannelPlot(object):
    plot = None
    channel = None
    min_value = 0
    max_value = 0
    lap = None
    sourceref = None
    chart_x_index = {}
    samples = 0

    def __init__(self, plot, channel, min_value, max_value, sourceref):
        self.plot = plot
        self.channel = channel
        self.min_value = min_value
        self.max_value = max_value
        self.sourceref = sourceref

    def __str__(self):
        return "{}_{}".format(str(self.sourceref), self.channel)

class LineChartMode(object):
    '''
    Describes the supported display modes for the chart
    '''
    time = 1
    distance = 2

class LineChart(ChannelAnalysisWidget):
    '''
    Displays a line chart capable of showing multiple channels from multiple laps
    '''
    color_sequence = ObjectProperty(None)
    _channel_plots = {}
    ZOOM_SCALING = 0.01
    TOUCH_ZOOM_SCALING = 0.000001
    MAX_SAMPLES_TO_DISPALY = 2000

    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs)
        self.register_event_type('on_marker')
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_motion=self.on_motion)

        self.metrics_base = MetricsBase()

        self.got_mouse = False
        self._touches = []
        self._initial_touch_distance = 0
        self._touch_offset = 0
        self._touch_distance = 0

        self.zoom_level = 1
        self.max_x = 0
        self.current_x = 0
        self.current_offset = 0
        self.marker_pct = 0
        self.line_chart_mode = LineChartMode.time

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y
        if self.collide_point(x, y):
            self.got_mouse = True
            touch.grab(self)
            if len(self._touches) == 1:
                self._initial_touch_distance = self._touches[0].distance(touch)
                self._touch_offset = self.current_offset
                self._touch_distance = self.current_x

            self._touches.append(touch)

            super(LineChart, self).on_touch_down(touch)
            return True
        else:
            super(LineChart, self).on_touch_down(touch)
            return False

    def on_touch_up(self, touch):
        self.got_mouse = False
        x, y = touch.x, touch.y

        # remove it from our saved touches
        if touch in self._touches:  # and touch.grab_state:
            touch.ungrab(self)
            self._touches.remove(touch)

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            return True

    def on_motion(self, instance, event, motion_event):
        if self.got_mouse and motion_event.x > 0 and motion_event.y > 0 and self.collide_point(motion_event.x, motion_event.y):
            chart = self.ids.chart
            try:
                zoom_scaling = self.max_x * self.ZOOM_SCALING
                button = motion_event.button
                zoom = self.marker_pct
                zoom_right = 1 / zoom
                zoom_left = 1 / (1 - zoom)
                zoom_left = zoom_left * zoom_scaling
                zoom_right = zoom_right * zoom_scaling

                if button == 'scrollup':
                    self.current_x += zoom_right
                    self.current_offset -= zoom_left
                else:
                    if button == 'scrolldown' and self.current_offset < self.current_x:
                        self.current_x -= zoom_right
                        self.current_offset += zoom_left

                self.current_x = self.max_x if self.current_x > self.max_x else self.current_x
                self.current_offset = 0 if self.current_offset < 0 else self.current_offset

                chart.xmax = self.current_x
                chart.xmin = self.current_offset
            except:
                pass  # no scrollwheel support

    def on_marker(self, marker_event):
        pass

    def dispatch_marker(self, x, y):
        mouse_x = x - self.pos[0]
        width = self.size[0]
        pct = mouse_x / width
        self.marker_pct = pct
        data_index = self.current_offset + (pct * (self.current_x - self.current_offset))
        self.ids.chart.marker_x = data_index
        for channel_plot in self._channel_plots.itervalues():
            try:
                value_index = bisect.bisect_right(channel_plot.chart_x_index.keys(), data_index)
                index = channel_plot.chart_x_index.values()[value_index]
                marker = MarkerEvent(int(index), channel_plot.sourceref)
                self.dispatch('on_marker', marker)
            except IndexError:
                pass  # don't update marker for values that don't exist.


    def on_touch_move(self, touch):
        x, y = touch.x, touch.y
        if self.collide_point(x, y):
            touches = len(self._touches)
            if touches == 1:
                # regular dragging / updating marker
                self.dispatch_marker(x, y)
            elif touches == 2:
                zoom_scaling = self.max_x * self.TOUCH_ZOOM_SCALING
                # handle pinch zoom
                touch1 = self._touches[0]
                touch2 = self._touches[1]
                distance = touch1.distance(touch2)
                delta = distance - self._initial_touch_distance
                delta = delta * (float(self.size[0]) * zoom_scaling)

                # zoom around a dynamic center between two touch points
                touch_center_x = touch1.x + ((touch2.x - touch1.x) / 2)
                width = self.size[0]
                pct = touch_center_x / width
                zoom_right = 1 / pct
                zoom_left = 1 / (1 - pct)
                zoom_left = zoom_left * delta
                zoom_right = zoom_right * delta

                self.current_x = self._touch_distance - zoom_right
                self.current_offset = self._touch_offset + zoom_left

                # Rail the zooming
                self.current_x = self.max_x if self.current_x > self.max_x else self.current_x
                self.current_x = self.current_offset + zoom_scaling if self.current_x < self.current_offset else self.current_x
                self.current_offset = 0 if self.current_offset < 0 else self.current_offset
                self.current_offset = self.current_x + zoom_scaling if self.current_offset > self.current_x else self.current_offset

                chart = self.ids.chart
                chart.xmax = self.current_x
                chart.xmin = self.current_offset
            return True

    def on_mouse_pos(self, x, pos):
        if len(self._touches) > 1:
            return False
        if not self.collide_point(pos[0], pos[1]):
            return False

        self.dispatch_marker(pos[0] * self.metrics_base.density, pos[1] * self.metrics_base.density)

    def remove_channel(self, channel, source_ref):
        remove = []
        for channel_plot in self._channel_plots.itervalues():
            if channel_plot.channel == channel and str(source_ref) == str(channel_plot.sourceref):
                remove.append(channel_plot)

        for channel_plot in remove:
            self.ids.chart.remove_plot(channel_plot.plot)
            del(self._channel_plots[str(channel_plot)])

        self._update_max_chart_x()

    def _update_max_chart_x(self):
        '''
        Reset max chart X dimension for the currently selected plots
        '''
        max_chart_x = 0
        for plot in self._channel_plots.itervalues():
            # Find the largest chart_x for all of the active plots
            chart_x_index = plot.chart_x_index
            last = next(reversed(chart_x_index))
            chart_x = last
            if chart_x and chart_x > max_chart_x:
                max_chart_x = chart_x

        # update chart zoom range
        self.current_offset = 0
        self.current_x = max_chart_x
        self.max_x = max_chart_x

        self.ids.chart.xmin = self.current_offset
        self.ids.chart.xmax = self.current_x


    def _add_channels_results_time(self, channels, query_data):
        try:
            time_data_values = query_data['Interval']
            for channel in channels:
                chart = self.ids.chart
                channel_data_values = query_data[channel]
                channel_data = channel_data_values.values
                #If we queried a channel that has no sample results, skip adding the plot
                if len(channel_data) == 0 or channel_data[0] is None:
                    continue

                key = channel_data_values.channel + str(channel_data_values.source)
                plot = SmoothLinePlot(color=self.color_sequence.get_color(key))
                channel_plot = ChannelPlot(plot,
                                           channel_data_values.channel,
                                           channel_data_values.min,
                                           channel_data_values.max,
                                           channel_data_values.source)

                chart.add_plot(plot)
                points = []
                time_index = OrderedDict()
                sample_index = 0
                time_data = time_data_values.values
                sample_count = len(time_data)
                if sample_count > self.MAX_SAMPLES_TO_DISPALY:
                    interval = int(sample_count / self.MAX_SAMPLES_TO_DISPALY)
                    Logger.info('LineChart: reducing resolution by a factor of {}'.format(interval))
                else:
                    interval = 1
                start_time = time_data[0]
                while sample_index < sample_count:
                    sample = channel_data[sample_index]
                    time = time_data[sample_index] - start_time
                    points.append((time, sample))
                    time_index[time] = sample_index
                    sample_index += interval

                channel_plot.chart_x_index = time_index
                channel_plot.samples = sample_index
                plot.ymin = channel_data_values.min
                plot.ymax = channel_data_values.max
                plot.points = points
                self._channel_plots[str(channel_plot)] = channel_plot

                # sync max chart x dimension
                self._update_max_chart_x()
        finally:
            ProgressSpinner.decrement_refcount()


    def _add_channels_results(self, channels, query_data):
        try:
            distance_data_values = query_data['Distance']
            for channel in channels:
                chart = self.ids.chart
                channel_data_values = query_data[channel]

                key = channel_data_values.channel + str(channel_data_values.source)
                plot = SmoothLinePlot(color=self.color_sequence.get_color(key))
                channel_plot = ChannelPlot(plot,
                                           channel_data_values.channel,
                                           channel_data_values.min,
                                           channel_data_values.max,
                                           channel_data_values.source)

                chart.add_plot(plot)
                points = []
                distance_index = OrderedDict()
                sample_index = 0
                distance_data = distance_data_values.values
                channel_data = channel_data_values.values
                for sample in channel_data:
                    distance = distance_data[sample_index]
                    points.append((distance, sample))
                    distance_index[distance] = sample_index
                    sample_index += 1

                channel_plot.chart_x_index = distance_index
                channel_plot.samples = sample_index
                plot.ymin = channel_data_values.min
                plot.ymax = channel_data_values.max
                plot.points = points
                self._channel_plots[str(channel_plot)] = channel_plot

                # sync max chart distances
                self._update_max_chart_x()
        finally:
            ProgressSpinner.decrement_refcount()

    def _add_unselected_channels(self, channels, source_ref):
        ProgressSpinner.increment_refcount()
        def get_results(results):
            # clone the incoming list of channels and pass it to the handler
            Clock.schedule_once(lambda dt: self._add_channels_results_time(channels[:], results))
        self.datastore.get_channel_data(source_ref, ['Interval', 'Distance'] + channels, get_results)
    
    def _customized(self, instance, values):
        updated_channels = values.current_channels
        self.select_channels(updated_channels)
        self.dispatch('on_channel_selected', updated_channels)
    
    def on_options(self, *args):
        params = CustomizeParams(settings=self.settings, datastore=self.datastore)
        values = CustomizeValues(list(self.selected_channels), self.line_chart_mode)

        content = OptionsView(values)
        content.add_options_screen(CustomizeChannelsScreen(name='Channels', params=params, values=values), ChannelsOptionsButton())
        content.add_options_screen(CustomizeChartScreen(name='Chart', params=params, values=values), ChartOptionsButton())

        popup = Popup(title="Customize Chart", content=content, size_hint=(0.7, 0.7))
        content.bind(on_customized=self._customized)
        content.bind(on_close=lambda *args:popup.dismiss())
        popup.open()
            
        
class CustomizeParams(object):
    '''
    A container class for holding multiple parameter for customization dialog
    '''
    def __init__(self, settings, datastore,  **kwargs):
        self.settings = settings
        self.datastore = datastore

class CustomizeValues(object):
    '''
    A container class for holding customization values
    '''
    def __init__(self, current_channels, line_chart_mode, **kwargs):
        self.current_channels = current_channels
        self.line_chart_mode = line_chart_mode

class ChannelsOptionsButton(LabelIconButton):
    Builder.load_string('''
<ChannelsOptionsButton>:
    title: 'Channels'
    icon_size: self.height * .9
    title_font_size: self.height * 0.6
    icon: u'\uf06d'    
    ''')

class ChartOptionsButton(LabelIconButton):
    Builder.load_string('''
<ChartOptionsButton>:
    title: 'Chart'
    icon_size: self.height * .9
    title_font_size: self.height * 0.6
    icon: u'\uf018'    
    ''')

class CustomizeChartScreen(BaseOptionsScreen):
    '''
    The customization view for customizing the chart options
    '''
    Builder.load_string('''
<CustomizeChartScreen>:
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: 'customize chart'
    ''')

    def __init__(self, params, values, **kwargs):
        super(CustomizeChartScreen, self).__init__(params, values, **kwargs)

    def on_enter(self):
        if self.initialized == False:
            pass

class CustomizeChannelsScreen(BaseOptionsScreen):
    '''
    The customization view for customizing the channels
    '''
    Builder.load_string('''
<CustomizeChannelsScreen>:
    ''')

    def __init__(self, params, values, **kwargs):
        super(CustomizeChannelsScreen, self).__init__(params, values, **kwargs)
        self.values = values
        content = CustomizeChannelsView(settings=params.settings, datastore=params.datastore, current_channels=values.current_channels)
        content.bind(on_channels_customized=self.on_modified)
        self.add_widget(content)
                
                
    def on_modified(self, *args):
        self.values.current_channels = args[1]
        super(CustomizeChannelsScreen, self).on_modified(*args)
        
    def on_enter(self):
        if self.initialized == False:
            pass

