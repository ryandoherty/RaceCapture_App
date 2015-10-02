import kivy
kivy.require('1.9.0')
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from installfix_garden_graph import Graph, MeshLinePlot
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.uix.track.trackmap import TrackMap

ANALYSIS_VIEW_KV = 'autosportlabs/racecapture/views/analysis/analysisview.kv'

class AnalysisView(Screen):
    _settings = None
    _databus = None
    _trackmanager = None

    def __init__(self, **kwargs):
        Builder.load_file(ANALYSIS_VIEW_KV)
        super(AnalysisView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self._trackmanager = kwargs.get('trackmanager')
        self.init_view()
    
    def on_tracks_updated(self, track_manager):
        tracks = track_manager.track_ids

#        if len(tracks) > 0:
#            trackId = track_manager.getAllTrackIds()[0]
#            track = track_manager.getTrackById(trackId)
#            self.ids.trackview.initMap(track)
#            self._trackmanager = track_manager

    def init_view(self):
        pass
