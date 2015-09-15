import kivy
kivy.require('1.9.0')
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color, Line
from kivy.core.window import Window
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.uix.track.trackmap import TrackMap
from utils import *

Builder.load_file('autosportlabs/uix/track/racetrackview.kv')
        
class RaceTrackView(BoxLayout):

    SCROLL_FACTOR = 0.15
    def __init__(self, **kwargs):
        super(RaceTrackView, self).__init__(**kwargs)
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
        

