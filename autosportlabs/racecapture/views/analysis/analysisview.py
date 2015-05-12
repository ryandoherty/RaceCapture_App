import os.path
from threading import Thread
import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.views.analysis.analysismap import AnalysisMap
from autosportlabs.racecapture.views.analysis.addstreamview import AddStreamView
from autosportlabs.racecapture.views.analysis.sessionbrowser import SessionBrowser, LapNode
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent, SourceRef
from autosportlabs.racecapture.views.analysis.linechart import LineChart
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.geo.geopoint import GeoPoint


Builder.load_file('autosportlabs/racecapture/views/analysis/analysisview.kv')

class AnalysisView(Screen):
    INIT_DATASTORE_TIMEOUT = 10.0
    _settings = None
    _databus = None
    _trackmanager = None
    _datastore = DataStore()
    _session_location_cache = {}
    _popup = None

    def __init__(self, **kwargs):
        super(AnalysisView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self._trackmanager = kwargs.get('trackmanager')
        self.init_view()

    def on_tracks_updated(self, track_manager):
        
        self.ids.analysismap.track_manager = track_manager

    def open_datastore(self):
        pass

    def on_add_stream(self, *args):
        self.show_add_stream_dialog()
                
    def on_stream_connected(self, *args):
        self._dismiss_popup()
        self.refresh_session_list()
        
    def show_add_stream_dialog(self):
        content = AddStreamView(settings=self._settings, datastore=self._datastore)
        content.bind(on_stream_connected=self.on_stream_connected)

        #content = Label(text='hello')
        popup = Popup(title="Add Telemetry Stream", content=content, size_hint=(0.7, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup

    def init_datastore(self):
        def _init_datastore(dstore_path):
            if os.path.isfile(dstore_path):
                self._datastore.open_db(dstore_path)
            else:
                print('creating datastore...')
                self._datastore.new(dstore_path)
            Clock.schedule_once(lambda dt: self.refresh_session_list())

        dstore_path = self._settings.userPrefs.get_datastore_location()
        print "Datastore Path:", dstore_path
        t = Thread(target=_init_datastore, args=(dstore_path,))
        t.daemon = True
        t.start()
        
    def refresh_session_list(self):
        try:
            sessions = self._datastore.get_sessions()
            f = Filter().gt('LapCount', 0)
            sessions_view = self.ids.sessions
            sessions_view.clear_sessions()
            for session in sessions:
                session_node = sessions_view.append_session(name=session.name, notes=session.notes)
                
                dataset = self._datastore.query(sessions=[session.ses_id],
                                        channels=['LapCount', 'LapTime'],
                                        data_filter=f,
                                        distinct_records=True)
        
                records = dataset.fetch_records()
                for r in records:
                    lapcount = r[1]
                    laptime = r[2]
                    sessions_view.append_lap(session_node, lapcount, laptime)
        except Exception as e:
            print("unable to fetch laps: " + str(e))
        
    def init_view(self):
        self.init_datastore()
        mainchart = self.ids.mainchart
        mainchart.settings = self._settings
        mainchart.datastore = self._datastore

    def on_channel_selected(self, instance, value):
        if value is not None:
            self._do_query(instance, value)

    def on_marker(self, instance, marker):
        source = marker.sourceref
        cache = self._session_location_cache.get(source.session)
        if cache != None:
            point = cache[marker.data_index]
            self.ids.analysismap.update_reference_mark(source, point)
        
    def _do_query(self, instance, channel):
        lap = 3
        session = 1
        f = Filter().eq('LapCount', lap)
        dataset = self._datastore.query(sessions=[session],
                         channels=['Distance', channel], data_filter=f)
        
        records = dataset.fetch_records()
        source = SourceRef(lap, session)
        self._sync_analysis_map(session)
        self._update_location_cache(session)
        
    def _update_location_cache(self, session):
        cache = self._session_location_cache.get(session)
        if cache == None:
            f = Filter().neq('Latitude', 0).and_().neq('Longitude', 0)
            dataset = self._datastore.query(sessions = [session], 
                                            channels = ["Latitude", "Longitude"], 
                                            data_filter = f)
            records = dataset.fetch_records()
            cache = []
            for r in records:
                lat = r[1]
                lon = r[2]
                cache.append(GeoPoint.fromPoint(lat, lon))
            self._session_location_cache[session]=cache
    
    def _sync_analysis_map(self, session):
        lat_avg = self._datastore.get_channel_average("Latitude", [session])
        lon_avg = self._datastore.get_channel_average("Longitude", [session])
        self.ids.analysismap.select_map(lat_avg, lon_avg)
        

    def popup_dismissed(self, *args):
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup is not None:
            self._popup.dismiss()
            self._popup = None

        
