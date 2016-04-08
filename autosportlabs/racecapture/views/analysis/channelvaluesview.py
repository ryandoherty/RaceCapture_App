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
import kivy
kivy.require('1.9.1')
from kivy.logger import Logger
from kivy.graphics import Color
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from autosportlabs.racecapture.views.analysis.analysiswidget import ChannelAnalysisWidget
from autosportlabs.uix.gauge.bargraphgauge import BarGraphGauge

Builder.load_file('autosportlabs/racecapture/views/analysis/channelvaluesview.kv')
    
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
        self.lap_view.text = str(int(value))

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

    @property
    def minval(self):
        return self.value_view.minval

    @minval.setter
    def minval(self, value):
        self.value_view.minval = value

    @property
    def maxval(self):
        return self.value_view.maxval

    @maxval.setter
    def maxval(self, value):
        self.value_view.maxval = value


class ChannelValuesView(ChannelAnalysisWidget):
    '''
    Shows a list of digital gauges for a combination of session / laps for selected laps
    '''
    color_sequence = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ChannelValuesView, self).__init__(**kwargs)
        self.channel_stats = {}
        self._channel_stat_widgets = {}

    def update_reference_mark(self, source, point):
        channel_data = self.channel_stats.get(str(source))
        if channel_data:
            for channel, channel_data in channel_data.iteritems():
                key = channel + str(source)
                widget = self._channel_stat_widgets.get(key)
                values = channel_data.values
                try:
                    value = str(values[point])
                except IndexError:
                    value = values[len(values) - 1]
                widget.value = value
                

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
                session_id = channel_data.source.session
                session = self.datastore.get_session_by_id(session_id, self.sessions)
                view.session = session.name
                view.minval = channel_data.min
                view.maxval = channel_data.max
                self._channel_stat_widgets[key] = view
                
        channels_grid.clear_widgets()
        for key in iter(sorted(self._channel_stat_widgets.iterkeys())):
            channels_grid.add_widget(self._channel_stat_widgets[key])

    def _add_channels_results(self, channels, channel_data):
        for channel in channels:
            self._add_channel_results(channel, channel_data)

    def _add_channel_results(self, channel, channel_data):
        '''
        Add the specified ChannelData to the dict of channel_stats, keyed by the lap/session source
        Organization is: dict of channel_stats keyed by source (lap/session key), each having a dict of ChannelData objects keyed by channel name
        '''
        channel_data_values = channel_data[channel]
        source_key = str(channel_data_values.source)
        channels = self.channel_stats.get(source_key)
        if not channels:
            channels = {} #looks like we're adding it for the first time for this source
            self.channel_stats[source_key] = channels
        channels[channel_data_values.channel] = channel_data_values
        self._refresh_channels()

    def add_channels(self, channels, source_ref):
        def get_results(results):
            Clock.schedule_once(lambda dt: self._add_channels_results(channels, results))

        self.datastore.get_channel_data(source_ref, channels, get_results)
    
    def refresh_view(self):
        self._refresh_channels()
        
    def remove_channel(self, channel, source_ref):
        source_key = str(source_ref)
        channels = self.channel_stats.get(source_key)
        channels.pop(channel, None)

                
                