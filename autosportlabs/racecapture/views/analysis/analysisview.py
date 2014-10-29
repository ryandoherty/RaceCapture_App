import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from installfix_garden_graph import Graph, MeshLinePlot
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.uix.track.trackmap import TrackMap

Builder.load_file('autosportlabs/racecapture/views/analysis/analysisview.kv')

class AnalysisView(Screen):
    _settings = None
    _databus = None
    _trackmanager = None
    
    def __init__(self, **kwargs):
        super(AnalysisView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self._trackmanager = kwargs.get('trackmanager')
        self.init_view()
    
    def on_tracks_updated(self, trackmanager):
        trackId = trackmanager.getAllTrackIds()[0]
        track = trackmanager.getTrackById(trackId)
        self.ids.trackview.initMap(track)        
        self._trackmanager = trackmanager

    def init_view(self):
        pass
