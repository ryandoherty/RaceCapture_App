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
class SourceRef(object):
    '''
    Contains a references to a data source
    '''
    lap = 0
    session = 0
    def __init__(self, lap, session):
        self.lap = int(lap)
        self.session = (session)
   
    def __str__(self):
        return "{}_{}".format(self.lap, self.session)
    
class MarkerEvent(object):
    '''
    Describes an event to synchronize views
    '''     
    data_index = 0
    sourceref = None
    def __init__(self, data_index, sourceref):
        self.data_index = data_index
        self.sourceref = sourceref
        