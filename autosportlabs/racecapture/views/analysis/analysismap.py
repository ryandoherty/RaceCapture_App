from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from autosportlabs.uix.track.racetrackview import RaceTrackView
from kivy.properties import ObjectProperty
from kivy.app import Builder

Builder.load_file('autosportlabs/racecapture/views/analysis/analysismap.kv')
class AnalysisMap(AnalysisWidget):
    track_manager = ObjectProperty(None)
        
        
    def on_track_manager(self, instance, value):
        tracks = self.track_manager.getAllTrackIds()
        if len(tracks) > 0:
            trackId = self.track_manager.getAllTrackIds()[0]
            track = self.track_manager.getTrackById(trackId)
            self.ids.track.initMap(track)
