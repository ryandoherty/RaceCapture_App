#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
#have received a copy of the GNU General Public License along with
#this code. If not, see <http://www.gnu.org/licenses/>.
import kivy
import math
from autosportlabs.uix.color import colorgradient
kivy.require('1.9.0')
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.app import Builder
from kivy.metrics import sp
from kivy.properties import ListProperty, NumericProperty
from kivy.graphics import Color, Line, Bezier, Rectangle
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.uix.color.colorgradient import HeatColorGradient, SimpleColorGradient
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
    #min / max for heat map range
    heat_min = NumericProperty(0.0)
    heat_max = NumericProperty(100.0)
    
    track_color = ListProperty([1.0, 1.0, 1.0, 0.5])
    
    MIN_PADDING = sp(1)
    DEFAULT_TRACK_WIDTH_SCALE = 0.01
    DEFAULT_MARKER_WIDTH_SCALE = 0.02
    DEFAULT_PATH_WIDTH_SCALE = 0.004
    DEFAULT_HEAT_WIDTH_SCALE = 0.01
    HEAT_MAP_WIDTH_STEP = 2

    def __init__(self, **kwargs):
        super(TrackMap, self).__init__(**kwargs)
        self.bind(pos=self._update_map)
        self.bind(size=self._update_map)

        self.track_width_scale = self.DEFAULT_TRACK_WIDTH_SCALE
        self.marker_width_scale = self.DEFAULT_MARKER_WIDTH_SCALE
        self.path_width_scale = self.DEFAULT_PATH_WIDTH_SCALE
        self.heat_width_scale = self.DEFAULT_HEAT_WIDTH_SCALE
        
        #these manage rendering of the points
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

    def setTrackPoints(self, geoPoints):
        '''
        Set the points for the track map
        :param geoPoints The list of points for the map
        :type geoPoints list
        '''
        self._gen_map_points(geoPoints)
        self._update_map()

    def get_path(self, key):
        '''
        Fetch a path by the specified key
        :param key the key representing the path
        :type key string
        :returns the TrackPath object matching the key, or None 
        '''
        return self._paths.get(key)
    
    def add_path(self, key, path, color):
        '''
        Add the specified path to the trackmap
        :param key the key identifying the path
        :type key string
        :param path a list of points representing the path
        :type path list of GeoPoint objects
        :param color the color of the path
        :type color list rgba colors
        '''
        points = []
        min_XY = self._min_XY
        max_XY = self._max_XY

        for geo_point in path:
            point = self._project_point(geo_point)
            min_XY.x = point.x if min_XY.x == -1 else min(min_XY.x, point.x)
            min_XY.y = point.y if min_XY.y == -1 else min(min_XY.y, point.y)
            points.append(point);

        # now, we need to keep track the max X and Y values
        for point in points:
            point.x = point.x - min_XY.x
            point.y = point.y - min_XY.y
            max_XY.x = point.x if max_XY.x == -1 else max(max_XY.x, point.x)
            max_XY.y = point.y if max_XY.y == -1 else max(max_XY.y, point.y)

        self._min_XY = min_XY
        self._max_XY = max_XY

        self._paths[key] = TrackPath(points, color)
        self._update_map()

    def set_heat_range(self, min_range, max_range):
        '''
        Set the min/max range for heat map mode
        :param min_range - minimum channel value
        :type min_range float
        :param max_range - maximum channel value
        :type max_range float
        '''
        self.heat_min = min_range
        self.heat_max = max_range
        
    def add_heat_values(self, key, heat_map_values):
        '''
        Add the point values for the specified key
        :param key The key referencing the heat map values
        :type key string
        :param heat_map_values A list of values. The number of values should correspond to exactly the number of points for the path matching the same key in path.
        :type heat_map_values list
        '''
        self._heat_map_values[key] = heat_map_values
        self._draw_current_map()

    def remove_heat_values(self, key):
        '''
        Remove the specified heat values 
        :param key the key for set of heat values to remove
        :type key string
        '''
        self._heat_map_values.pop(key, None)
        self._draw_current_map()

    def remove_path(self, key):
        '''
        Remove the specified path. 
        :param key the key representing the path to remove
        :type key string 
        '''
        self._paths.pop(key, None)
        self._scaled_paths.pop(key, None)
        #Also remove heat values since they are paired with the same key
        self._heat_map_values.pop(key, None)  
        self._draw_current_map()

    def add_marker(self, key, color):
        '''
        Adds a marker to be displayed on the track map
        :param key The key representing the marker
        :type key string
        :param color color of the marker
        :type color list
        '''
        self._marker_points[key] = MarkerPoint(color)

    def remove_marker(self, key):
        '''
        Removes the specified marker
        :param key representing the marker to remove
        :type key string
        '''
        self._marker_points.pop(key, None)
        self._marker_locations.pop(key, None)
        self._draw_current_map()

    def get_marker(self, key):
        '''
        Fetch the specified marker
        :param key the key of ther marker to fetch;
        :type key string 
        :returns MarkerPoint the MarkerPoint object for the key, or None if key doesn't exist
        '''
        return self._marker_points.get(key)

    def update_marker(self, key, geoPoint):
        '''
        Update the marker to the specified position
        :param key The key of the marker
        :type key string
        :param geoPoint the point for the updated position
        :type GeoPoint
        '''
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
        
    def _update_map(self, *args):
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

        heat_width_step = sp(self.HEAT_MAP_WIDTH_STEP)
        path_count = len(self._scaled_paths.keys())
        heat_width = sp(self.heat_width_scale * self.height) + ((path_count - 1) * heat_width_step)
        
        with self.canvas:
            Color(*self.track_color)
            Line(points=self._scaled_map_points, width=sp(self.track_width_scale * self.height), closed=True, cap='round', joint='round')

            color_gradient = HeatColorGradient()
                
            #draw all of the traces
            for key, path_points in self._scaled_paths.iteritems():
                heat_path = self._heat_map_values.get(key)
                if heat_path:
                    #draw heat map
                    point_count = len(path_points)
                    heat_min = self.heat_min
                    heat_range = self.heat_max - heat_min
                    value_index = 0
                    current_heat_pct = 0
                    i=0
                    line_points = []
                    
                    try:
                        line_points.extend([path_points[i], path_points[i + 1]])
                        current_heat_pct = int(((heat_path[value_index] - heat_min) / heat_range) * 100.0)
                        while i < point_count - 2:
                            heat_value = heat_path[value_index]
                            heat_pct = int(((heat_value - heat_min) / heat_range) * 100.0)
                            if heat_pct != current_heat_pct:
                                heat_color = color_gradient.get_color_value(heat_pct / 100.0)
                                Color(*heat_color)
                                Line(points=line_points, width=heat_width, closed=False, joint='miter', cap='round')
                                line_points=[path_points[i-2], path_points[i-1]]
                                current_heat_pct = heat_pct
                            line_points.extend([path_points[i], path_points[i + 1]])
                            value_index += 1
                            i += 2
                        heat_width -= heat_width_step
                    except IndexError: #if the number of heat values mismatch the heat map points, terminate early
                        pass
                else:
                    #draw regular map trace
                    Color(*self._paths[key].color)
                    Line(points=path_points, width=sp(self.path_width_scale * self.height), closed=True, cap='square', joint='miter')

            #draw the markers
            marker_size = self.marker_width_scale * self.height
            for key, marker_point in self._marker_points.iteritems():
                scaled_point = self._scale_point(marker_point, self.height, left, bottom)
                Color(*marker_point.color)
                self._marker_locations[key] = Line(circle=(scaled_point.x, scaled_point.y, marker_size), width=marker_size, closed=True)
        
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

    def _gen_map_points(self, geo_points):
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
