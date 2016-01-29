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
import os.path
from threading import Thread
import kivy
kivy.require('1.9.0')
from kivy.logger import Logger
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from autosportlabs.racecapture.views.analysis.analysisdata import CachingAnalysisDatastore
from autosportlabs.racecapture.views.analysis.analysismap import AnalysisMap
from autosportlabs.racecapture.views.analysis.channelvaluesview import ChannelValuesView
from autosportlabs.racecapture.views.analysis.addstreamview import AddStreamView
from autosportlabs.racecapture.views.analysis.sessionbrowser import SessionBrowser
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent, SourceRef
from autosportlabs.racecapture.views.analysis.linechart import LineChart
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.uix.color.colorsequence import ColorSequence
from autosportlabs.racecapture.theme.color import ColorScheme
from autosportlabs.help.helpmanager import HelpInfo
import traceback

ANALYSIS_VIEW_KV = 'autosportlabs/racecapture/views/analysis/analysisview.kv'

class AnalysisView(Screen):
    SUGGESTED_CHART_CHANNELS = ['Speed']
    INIT_DATASTORE_TIMEOUT = 10.0
    _settings = None
    _databus = None
    _track_manager = None
    _popup = None
    _color_sequence = ColorSequence()
    sessions = ObjectProperty(None)

    def __init__(self, **kwargs):
        Builder.load_file(ANALYSIS_VIEW_KV)
        super(AnalysisView, self).__init__(**kwargs)
        self._datastore = CachingAnalysisDatastore()
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings') 
        self._track_manager = kwargs.get('track_manager')
        self.ids.sessions_view.bind(on_lap_selected=self.lap_selected)
        self.ids.channelvalues.color_sequence = self._color_sequence
        self.ids.mainchart.color_sequence = self._color_sequence
        self.stream_connecting = False
        self.init_view()

    def on_sessions(self, instance, value):
        self.ids.channelvalues.sessions = value
        
    def lap_selected(self, instance, source_ref, selected):
        source_key = str(source_ref)
        if selected:
            self.ids.mainchart.add_lap(source_ref)
            self.ids.channelvalues.add_lap(source_ref)
            map_path_color = self._color_sequence.get_color(source_key)
            self.ids.analysismap.add_reference_mark(source_key, map_path_color)
            self._sync_analysis_map(source_ref.session)
            self._datastore.get_location_data(source_ref, lambda x: self.ids.analysismap.add_map_path(source_ref, x, map_path_color))

        else:
            self.ids.mainchart.remove_lap(source_ref)
            self.ids.channelvalues.remove_lap(source_ref)
            self.ids.analysismap.remove_reference_mark(source_key)
            self.ids.analysismap.remove_map_path(source_ref)
    
    def on_tracks_updated(self, track_manager):
        self.ids.analysismap.track_manager = track_manager

    def on_channel_selected(self, instance, value):
        self.ids.channelvalues.merge_selected_channels(value)

    def on_marker(self, instance, marker):
        source = marker.sourceref
        cache = self._datastore.get_location_data(source)
        if cache != None:
            try:
                point = cache[marker.data_index]
            except IndexError:
                point = cache[len(cache) - 1]
            self.ids.analysismap.update_reference_mark(source, point)
            self.ids.channelvalues.update_reference_mark(source, marker.data_index)
                          
    def _sync_analysis_map(self, session):
        analysis_map = self.ids.analysismap
        if not analysis_map.track:
            lat_avg, lon_avg = self._datastore.get_location_center([session])
            analysis_map.select_map(lat_avg, lon_avg)

    def open_datastore(self):
        pass

    def on_add_stream(self, *args):
        self.show_add_stream_dialog()
                
    def on_stream_connected(self, instance, new_session_id):
        self.stream_connecting = False
        self._dismiss_popup()
        self.ids.sessions_view.refresh_session_list()
        self.check_load_suggested_lap(new_session_id)
    
    #The following selects a best lap if there are no other laps currently selected
    def check_load_suggested_lap(self, new_session_id):
        sessions_view = self.ids.sessions_view
        if len(sessions_view.selected_laps) == 0:
            best_lap = self._datastore.get_channel_min('LapTime', [new_session_id], ['LapCount'])
            if best_lap:
                best_lap_id = best_lap[1]
                Logger.info('AnalysisView: Convenience selected a suggested session {} / lap {}'.format(new_session_id, best_lap_id))
                main_chart = self.ids.mainchart
                main_chart.select_channels(AnalysisView.SUGGESTED_CHART_CHANNELS)
                self.ids.channelvalues.select_channels(AnalysisView.SUGGESTED_CHART_CHANNELS)
                sessions_view.select_lap(new_session_id, best_lap_id, True)
                HelpInfo.help_popup('suggested_lap', main_chart, arrow_pos='left_mid')
            else:
                Logger.warn('AnalysisView: Could not determine best lap for session {}'.format(new_session_id))
        
    def on_stream_connecting(self, *args):
        self.stream_connecting = True
        
    def show_add_stream_dialog(self):
        self.stream_connecting = False
        content = AddStreamView(settings=self._settings, datastore=self._datastore)
        content.bind(on_connect_stream_start=self.on_stream_connecting)
        content.bind(on_connect_stream_complete=self.on_stream_connected)
        
        popup = Popup(title="Add Telemetry Stream", content=content, size_hint=(0.7, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup

    def init_datastore(self):
        def _init_datastore(dstore_path):
            if os.path.isfile(dstore_path):
                self._datastore.open_db(dstore_path)
            else:
                Logger.info('AnalysisView: creating datastore...')
                self._datastore.new(dstore_path)
            self.ids.sessions_view.datastore = self._datastore

        dstore_path = self._settings.userPrefs.datastore_location
        Logger.info("AnalysisView: Datastore Path:" + str(dstore_path))
        t = Thread(target=_init_datastore, args=(dstore_path,))
        t.daemon = True
        t.start()
                
    def init_view(self):
        self.init_datastore()
        mainchart = self.ids.mainchart
        mainchart.settings = self._settings
        mainchart.datastore = self._datastore
        channelvalues = self.ids.channelvalues
        channelvalues.datastore = self._datastore
        channelvalues.settings = self._settings
        self.ids.analysismap.track_manager = self._track_manager
        self.ids.analysismap.datastore = self._datastore
        Clock.schedule_once(lambda dt: HelpInfo.help_popup('beta_analysis_welcome', self, arrow_pos='right_mid'), 0.5)


    def popup_dismissed(self, *args):
        if self.stream_connecting:
            return True
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup is not None:
            self._popup.dismiss()
            self._popup = None
