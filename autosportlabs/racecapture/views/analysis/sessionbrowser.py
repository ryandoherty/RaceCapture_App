import kivy
kivy.require('1.8.0')
from kivy.app import Builder

from kivy.uix.treeview import TreeView, TreeViewLabel

Builder.load_file('autosportlabs/racecapture/views/analysis/sessionbrowser.kv')

class SessionBrowser(object):
    
    def append_session(self, session):
        pass

    

