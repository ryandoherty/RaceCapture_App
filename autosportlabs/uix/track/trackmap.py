import kivy
import math
kivy.require('1.9.0')
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.app import Builder
from kivy.metrics import sp
from kivy.properties import ListProperty
from kivy.graphics import Color, Line, Bezier, Rectangle
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from utils import *

Builder.load_file('autosportlabs/uix/track/trackmap.kv')

class Point(object):
    x = 0.0
    y = 0.0
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
class MarkerPoint(Point):
    def __init__(self, color):
        super(MarkerPoint, self).__init__(0, 0)
        self.color = color
    
class TrackPath(object):
    def __init__(self, path, color):
        self.color = color
        self.path = path

class TrackMap(Widget):
    track_color = ListProperty([1.0, 1.0, 1.0, 0.5])
    MIN_PADDING = sp(1)
    DEFAULT_TRACK_WIDTH_SCALE = 0.01
    DEFAULT_MARKER_WIDTH_SCALE = 0.02
    DEFAULT_PATH_WIDTH_SCALE = 0.002
    DEFAULT_HEAT_WIDTH_SCALE = 0.005  

    def __init__(self, **kwargs):
        super(TrackMap, self).__init__(**kwargs)
        self.bind(pos=self.update_map)
        self.bind(size=self.update_map)

        self.track_width_scale = self.DEFAULT_TRACK_WIDTH_SCALE
        self.marker_width_scale = self.DEFAULT_MARKER_WIDTH_SCALE
        self.path_width_scale = self.DEFAULT_PATH_WIDTH_SCALE
        self.heat_width_scale = self.DEFAULT_HEAT_WIDTH_SCALE
        
        self._offset_point = Point(0,0)
        self._global_ratio = 0
        self._height_padding = 0
        self._width_padding = 0
        
        self._min_XY = Point(-1, -1)
        self._max_XY = Point(-1, -1)
    
        #The trackmap
        self._map_points = []
        self._scaled_map_points = []
    
        #The map _paths
        self._paths = {}
        self._scaled_paths = {}
        self._heat_map_values = {}
        
        #markers for trackmap
        self._marker_points = {}
        self._marker_locations = {}

    
    def on_trackColor(self, instance, value):
        self._draw_current_map()

    def add_path(self, key, path, color):
        points = []
        for geo_point in path:
            point = self._project_point(geo_point)
            points.append(point);

        min_x = self._min_XY.x
        min_y = self._min_XY.y

        for point in points:
            point.x = point.x - min_x
            point.y = point.y - min_y

        self._paths[key] = TrackPath(points, color)
        self.update_map()

    def add_heat_values(self, key, heat_map_values):
        self._heat_map_values[key] = heat_map_values
        self._draw_current_map()

    def remove_heat_values(self, key):
        self._heat_map_values.pop(key, None)
        self._draw_current_map()

    def remove_path(self, key):
        self._paths.pop(key, None)
        self._scaled_paths.pop(key, None)
        self._draw_current_map()

    def add_marker(self, key, color):
        self._marker_points[key] = MarkerPoint(color)

    def remove_marker(self, key):
        self._marker_points.pop(key, None)
        self._marker_locations.pop(key, None)
        self._draw_current_map()

    def get_marker(self, key):
        return self._marker_points.get(key)

    def update_marker(self, key, geoPoint):
        marker_point = self._marker_points.get(key)
        marker_location = self._marker_locations.get(key)
        if marker_point and marker_location:
            left = self.pos[0]
            bottom = self.pos[1]
            point = self._offset_track_point(self._project_point(geoPoint))
            marker_point.x = point.x
            marker_point.y = point.y
            scaled_point = self._scale_point(marker_point, self.height, left, bottom)

            marker_size = self.marker_width_scale * self.height
            marker_location.circle = (scaled_point.x, scaled_point.y, marker_size)
        
    def update_map(self, *args):
        
        padding_both_sides = self.MIN_PADDING * 2
        
        width = self.size[0]
        height = self.size[1]
        
        left = self.pos[0]
        bottom = self.pos[1]
        
        # the actual drawing space for the map on the image
        map_width = width - padding_both_sides;
        map_height = height - padding_both_sides;

        #determine the width and height ratio because we need to magnify the map to fit into the given image dimension
        map_width_ratio = float(map_width) / float(self._max_XY.x)
        map_height_ratio = float(map_height) / float(self._max_XY.y)

        # using different ratios for width and height will cause the map to be stretched. So, we have to determine
        # the global ratio that will perfectly fit into the given image dimension
        self._global_ratio = min(map_width_ratio, map_height_ratio)

        #now we need to readjust the padding to ensure the map is always drawn on the center of the given image dimension
        self._height_padding = (height - (self._global_ratio * self._max_XY.y)) / 2.0
        self._width_padding = (width - (self._global_ratio * self._max_XY.x)) / 2.0
        self._offset_point = self._min_XY
        
        #track outline
        points = self._map_points
        scaled_map_points = []
        for point in points:
            scaled_point = self._scale_point(point, self.height, left, bottom)
            scaled_map_points.append(scaled_point.x)
            scaled_map_points.append(scaled_point.y)
        self._scaled_map_points = scaled_map_points

        paths = self._paths
        scaled_paths = {}
        for key, track_path in paths.iteritems():
            scaled_path_points = []
            for point in track_path.path:
                scaled_path_point = self._scale_point(point, self.height, left, bottom)
                scaled_path_points.append(scaled_path_point.x)
                scaled_path_points.append(scaled_path_point.y)
            scaled_paths[key] = scaled_path_points

        self._scaled_paths = scaled_paths
        self._draw_current_map()

    def _draw_current_map(self):
        left = self.pos[0]
        bottom = self.pos[1]
        self.canvas.clear()

        with self.canvas:

            Color(*self.track_color)
            Line(points=self._scaled_map_points, width=sp(self.track_width_scale * self.height), closed=True, joint='round')

            #draw all of the traces
            for key, path_points in self._scaled_paths.iteritems():

                heat_path = self._heat_map_values.get(key)
                if heat_path:
                    #draw heat map
                    point_count = len(path_points)
                    value_index = 0
                    heat_value = 0
                    try:
                        for i in range(0, point_count - 2, 2):
                            x1 = path_points[i]
                            y1 = path_points[i + 1]
                            x2 = path_points[i + 2]
                            y2 = path_points[i + 3]
                            heat_value = heat_path[value_index]
                            heat_color = self._get_heat_map_color(heat_value / 100.0) #TODO get the channel meta min / max
                            Color(*heat_color)
                            Line(points=[x1, y1, x2, y2], width=sp(self.heat_width_scale * self.height), closed=False, joint='round')
                            value_index+=1
                    except IndexError: #if the number of heat values mismatch the heat map points, terminate early
                        pass
                else:
                    #draw regular map
                    Color(*self._paths[key].color)
                    Line(points=path_points, width=sp(self.path_width_scale * self.height), closed=True)

            #draw the markers
            marker_size = self.marker_width_scale * self.height
            for key, marker_point in self._marker_points.iteritems():
                scaled_point = self._scale_point(marker_point, self.height, left, bottom)
                Color(*marker_point.color)
                self._marker_locations[key] = Line(circle=(scaled_point.x, scaled_point.y, marker_size), width=marker_size, closed=True)

         
    def setTrackPoints(self, geoPoints):
        self.gen_map_points(geoPoints)
        self.update_map()
        
    def _offset_track_point(self, point):
        point.x = point.x - self._min_XY.x
        point.y = point.y - self._min_XY.y
        return point
        
    def _project_point(self, geo_point):
        latitude = geo_point.latitude * float(math.pi / 180.0)
        longitude = geo_point.longitude * float(math.pi / 180.0)
        point = Point(longitude, float(math.log(math.tan((math.pi / 4.0) + 0.5 * latitude))))
        return point;

    def _scale_point(self, point, height, left, bottom):
        adjusted_X = int((self._width_padding + (point.x * self._global_ratio))) + left
        #need to invert the Y since 0,0 starts at top left
        adjusted_Y = int((self._height_padding + (point.y * self._global_ratio))) + bottom
        return Point(adjusted_X, adjusted_Y)

    def gen_map_points(self, geo_points):
        points = []
        
        # min and max coordinates, used in the computation below
        min_XY = Point(-1, -1)
        max_XY = Point(-1, -1)
        
        for geo_point in geo_points:
            point = self._project_point(geo_point)
            min_XY.x = point.x if min_XY.x == -1 else min(min_XY.x, point.x)
            min_XY.y = point.y if min_XY.y == -1 else min(min_XY.y, point.y)
            points.append(point);
        
        # now, we need to keep track the max X and Y values
        for point in points:
            point.x = point.x - min_XY.x
            point.y = point.y - min_XY.y
            max_XY.x = point.x if max_XY.x == -1 else max(max_XY.x, point.x)
            max_XY.y = point.y if max_XY.y == -1 else max(max_XY.y, point.y);
                
        self._min_XY = min_XY
        self._max_XY = max_XY
        self._map_points =  points
        
    def _get_heat_map_color(self, value):
        colors = [[0,0,1,1], [0,1,0,1], [1,1,0,1], [1,0,0,1]]
        num_colors = len(colors)

        idx1 = 0
        idx2 = 0
        frac_between = 0.0

        if value <= 0:
            idx1 = idx2 = 0
        elif value >= 1:
            idx1 = idx2 = num_colors - 1
        else:
            value = value * (num_colors - 1)
            idx1  = int(math.floor(value))
            idx2  = idx1 + 1
            frac_between = value - float(idx1)

        red   = (colors[idx2][0] - colors[idx1][0]) * frac_between + colors[idx1][0];
        green = (colors[idx2][1] - colors[idx1][1]) * frac_between + colors[idx1][1];
        blue  = (colors[idx2][2] - colors[idx1][2]) * frac_between + colors[idx1][2];
        
        return [red, green, blue, 1.0]
