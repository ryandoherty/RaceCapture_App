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
from kivy.utils import get_color_from_hex as rgb

DEFAULT_COLOR_SEQUENCE = ['FFFFFF', '8A00B8', '3366FF', 'F5B800', '8AB800', 'f45b5b', 'ff0066']

class ColorSequence(object):
    color_index = 0
    colors = []
    color_map = {}

    def __init__(self, colors=DEFAULT_COLOR_SEQUENCE):
        self.colors = colors

    def get_color(self, key):
        color = self.color_map.get(key)
        if not color:
            index = self.color_index
            color = rgb(self.colors[index])
            index = index + 1 if index < len(self.colors) - 1 else 0
            self.color_index = index
            self.color_map[key] = color
        return color
        
        