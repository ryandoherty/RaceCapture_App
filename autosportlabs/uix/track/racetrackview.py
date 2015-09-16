import kivy
kivy.require('1.9.0')
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color, Line
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.uix.track.trackmap import TrackMap
from utils import *

Builder.load_file('autosportlabs/uix/track/racetrackview.kv')
        
class RaceTrackView(BoxLayout):
    def __init__(self, **kwargs):
        super(RaceTrackView, self).__init__(**kwargs)
        
    def loadTrack(self, track):
        self.initMap(track)
                
    def initMap(self, track):
        self.ids.trackmap.setTrackPoints(track.mapPoints)
        
    def remove_reference_mark(self, key):
        self.ids.trackmap.remove_marker(key)

    def add_reference_mark(self, key, color):
        trackmap = self.ids.trackmap
        if trackmap.get_marker(key) is None:
            trackmap.add_marker(key, color)

    def update_reference_mark(self, key, geo_point):
        trackmap = self.ids.trackmap
        trackmap.update_marker(key, geo_point)
        

