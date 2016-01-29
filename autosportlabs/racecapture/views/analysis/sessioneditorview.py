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
import os
from threading import Thread
import kivy
from kivy.uix.boxlayout import BoxLayout

kivy.require('1.9.0')
from kivy.app import Builder

Builder.load_file('autosportlabs/racecapture/views/analysis/sessioneditorview.kv')

class SessionEditorView(BoxLayout):
    def __init__(self, **kwargs):
        super(SessionEditorView, self).__init__(**kwargs)

    @property
    def session_name(self):
        return self.ids.session_name.text.strip()
    
    @session_name.setter
    def session_name(self, value):
        self.ids.session_name.text = value
    
    @property
    def session_notes(self):
        return self.ids.session_notes.text.strip()
    
    @session_notes.setter
    def session_notes(self, value):
        self.ids.session_notes.text = value
