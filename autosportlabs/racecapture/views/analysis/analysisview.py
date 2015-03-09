import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from autosportlabs.racecapture.datastore import DataStore, Filter
from autosportlabs.racecapture.views.analysis.analysismap import AnalysisMap
from autosportlabs.racecapture.views.analysis.sessionbrowser import SessionBrowser, LapNode
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent, SourceRef
from autosportlabs.racecapture.views.analysis.linechart import LineChart
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock

import os.path

from threading import Thread

Builder.load_file('autosportlabs/racecapture/views/analysis/analysisview.kv')


class LogImportWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(LogImportWidget, self).__init__(**kwargs)
        self._dstore = kwargs.get('datastore')
        self._dismiss = kwargs.get('dismiss_cb')
        self._settings = kwargs.get('settings')
        self.register_event_type('on_import_complete')

    def on_import_complete(self, *args):
        pass
    
    def close_dstore_select(self, *args):
        self._dstore_select.dismiss()
        self._dstore_select = None

    def set_dstore_path(self, instance):
        filename = os.path.join(instance.path, instance.filename)
        if not filename.endswith('.sq3'):
            filename = filename + '.sq3'
        self.ids['dstore_path'].text = filename
        self._dstore_select.dismiss()

    def select_dstore(self):
        ok_cb = self.close_dstore_select
        content = SaveDialog(ok=self.set_dstore_path,
                             cancel=self.close_dstore_select,
                             filters=['*' + '.sq3'])
        self._dstore_select = Popup(title="Select Datastore", content=content, size_hint=(0.9, 0.9))
        self._dstore_select.open()

    def close_log_select(self, *args):
        self._log_select.dismiss()
        self._log_select = None

    def set_log_path(self, instance):
        path = instance.selection[0]
        self.ids['log_path'].text = path
        self.ids['session_name'].text = os.path.basename(path) 
        
        self._log_select.dismiss()
        self.set_import_file_path(instance.path)

    def set_import_file_path(self, path):
        self._settings.userPrefs.set_pref('preferences', 'import_datalog_dir', path)
        
    def get_import_file_path(self):
        return self._settings.userPrefs.get_pref('preferences', 'import_datalog_dir')
 
    def select_log(self):
        ok_cb = self.close_log_select
        content = LoadDialog(ok=self.set_log_path,
                             cancel=self.close_log_select,
                             filters=['*' + '.log'],
                             user_path=self.get_import_file_path())
        self._log_select = Popup(title="Select Log", content=content, size_hint=(0.9, 0.9))
        self._log_select.open()

    def _loader_thread(self, logpath, session_name, session_notes):
        self._dstore.import_datalog(logpath, session_name, session_notes, self._update_progress)
        Clock.schedule_once(lambda dt: self.dispatch('on_import_complete'))
        self._dismiss()

    def _update_progress(self, percent_complete=0):
        if self.ids['current_status'].text != "Loading log records":
            self.ids['current_status'].text = "Loading log records"
        self.ids['log_load_progress'].value = int(percent_complete)

    def load_log(self):
        logpath = self.ids['log_path'].text
        session_name = self.ids['session_name'].text
        session_notes = self.ids['session_notes'].text
        
        dstore_path = self._settings.userPrefs.get_datastore_location()

        if logpath == '':
            alertPopup("No Log Specified",
                      "Please select a log file to import")
            return

        if not os.path.isfile(logpath):
            alertPopup("Invalid log specified",
                      "Unable to find specified log file: {}. \nAre you sure it exists?".format(logpath))
            return

        if self._dstore.db_path != dstore_path:
            if self._dstore.is_open:
                self._dstore.close()
            
            if os.path.isfile(dstore_path):
                self._dstore.open_db(dstore_path)
            else:
                self._dstore.new(dstore_path)

        print "loading log", self.ids['log_path'].text

        if session_name == '':
            alertPopup("No session name specified", "Please specify a name for this session")
            return

        self.ids['current_status'].text = "Initializing Datastore"

        t = Thread(target=self._loader_thread, args=(logpath, session_name, session_notes))
        t.daemon = True
        t.start()


class AnalysisView(Screen):
    INIT_DATASTORE_TIMEOUT = 10.0
    _settings = None
    _databus = None
    _trackmanager = None
    _datastore = DataStore()
    _session_location_cache = {}

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

    def on_import_complete(self, *args):
        print('import complete')
        self.refresh_session_list()
        
    def import_datalog(self):
        content = LogImportWidget(datastore=self._datastore, dismiss_cb=self.dismiss_popup, settings=self._settings)
        content.bind(on_import_complete=self.on_import_complete)
        
        self._popup = Popup(title="Import Datalog", content=content, size_hint=(0.6, 0.6))
        self._popup.open()

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

    def dismiss_popup(self, *args):
        self._popup.dismiss()

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
        instance.add_channel_data(records, channel, 0, 255, source)
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
        
        
        
