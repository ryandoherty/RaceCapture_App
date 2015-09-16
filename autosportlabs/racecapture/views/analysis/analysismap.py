from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from autosportlabs.uix.track.racetrackview import RaceTrackView
from kivy.properties import ObjectProperty
from kivy.app import Builder
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from kivy.core.window import Window

Builder.load_file('autosportlabs/racecapture/views/analysis/analysismap.kv')
class AnalysisMap(AnalysisWidget):
    SCROLL_FACTOR = 0.15
    track_manager = ObjectProperty(None)
        
    def __init__(self, **kwargs):
        super(AnalysisMap, self).__init__(**kwargs)
        Window.bind(on_motion=self.on_motion)

    def on_motion(self, instance, event, motion_event):
        if self.collide_point(motion_event.x, motion_event.y):
            scatter = self.ids.scatter
            button = motion_event.button
            scale = scatter.scale
            if button == 'scrollup':
                scale += self.SCROLL_FACTOR
            else:
                if button == 'scrolldown':
                    scale -= self.SCROLL_FACTOR
            if scale < self.SCROLL_FACTOR:
                scale = self.SCROLL_FACTOR
            scatter.scale = scale
        
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

    def add_map_path(self, source_key, path, color):
        self.ids.track.add_map_path(source_key, path, color)

    def remove_map_path(self, source_key):
        self.ids.track.remove_map_path(source_key)
