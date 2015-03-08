import kivy
kivy.require('1.8.0')
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color, Line
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.uix.track.trackmap import TrackMap
from autosportlabs.uix.color.colorsequence import ColorSequence
from utils import *

Builder.load_file('autosportlabs/uix/track/racetrackview.kv')
        
class RaceTrackView(BoxLayout):
    _color_sequence = ColorSequence()

    def __init__(self, **kwargs):
        super(RaceTrackView, self).__init__(**kwargs)

    def loadTrack(self, track):
        self.initMap(track)
                
    def initMap(self, track):
        self.ids.trackmap.setTrackPoints(track.mapPoints)
        
    def update_reference_mark(self, key, geo_point):
        trackmap = self.ids.trackmap
        if trackmap.get_marker(key) is None:
            trackmap.add_marker(key, self._color_sequence.get_next_color())
        trackmap.update_marker(key, geo_point)
        

