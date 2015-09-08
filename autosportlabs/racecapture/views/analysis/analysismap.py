from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from autosportlabs.uix.track.racetrackview import RaceTrackView
from kivy.properties import ObjectProperty
from kivy.app import Builder
from autosportlabs.racecapture.geo.geopoint import GeoPoint

Builder.load_file('autosportlabs/racecapture/views/analysis/analysismap.kv')
class AnalysisMap(AnalysisWidget):
    track_manager = ObjectProperty(None)
        
    def select_map(self, latitude, longitude):
        if self.track_manager:
            point = GeoPoint.fromPoint(latitude, longitude)
            track = self.track_manager.findNearbyTrack(point)
            if track != None:
                self.ids.track.initMap(track)

    def remove_reference_mark(self, source):
        self.ids.track.remove_reference_mark(source)

    def add_reference_mark(self, source, color):
        self.ids.track.add_reference_mark(source, color)

    def update_reference_mark(self, source, point):
        self.ids.track.update_reference_mark(str(source), point)
