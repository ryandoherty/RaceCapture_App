import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from installfix_garden_graph import Graph, MeshLinePlot
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.uix.track.trackmap import TrackMap
from autosportlabs.racecapture.datastore import DataStore
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout

Builder.load_file('autosportlabs/racecapture/views/analysis/analysisview.kv')

class LogImportWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(LogImportWidget, self).__init__(**kwargs)
        self._dstore = kwargs.get('datastore')
        
    pass

class AnalysisView(Screen):
    _settings = None
    _databus = None
    _trackmanager = None
    _datastore = DataStore()

    def __init__(self, **kwargs):
        super(AnalysisView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self._trackmanager = kwargs.get('trackmanager')
        self.init_view()
    
    def on_tracks_updated(self, track_manager):
        tracks = track_manager.getAllTrackIds()

        if len(tracks) > 0:
            trackId = track_manager.getAllTrackIds()[0]
            track = track_manager.getTrackById(trackId)
            self.ids.trackview.initMap(track)
            self._trackmanager = track_manager

    def open_datastore(self):
        pass

    def _log_import_thread(self):
        self._datastore.import_datalog
        pass

    def _start_log_import(self, instance):
        self._popup.dismiss()
        #The comma is necessary since we need to pass in a sequence of args
        t = Thread(target=self._log_import_thread, args=(instance,))
        t.daemon = True
        t.start()

        
    def import_datalog(self):
        content = LogImportWidget(datastore=self._datastore)

        self._popup = Popup(title="Import Datalog", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def init_view(self):
        pass
        
    def dismiss_popup(self, *args):
        self._popup.dismiss()
