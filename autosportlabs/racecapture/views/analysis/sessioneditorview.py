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
