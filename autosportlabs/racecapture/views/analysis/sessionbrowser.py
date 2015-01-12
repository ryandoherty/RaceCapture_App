import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewLabel

Builder.load_file('autosportlabs/racecapture/views/analysis/sessionbrowser.kv')

class SessionLapView(BoxLayout):
    def __init__(self, **kwargs):
        lap = kwargs.get('lap','')
        laptime = kwargs.get('laptime', '---')
        
        self.ids.lap.text = str(lap)
        self.ids.laptime.text = str(laptime)
    
class TreeSessionLapView(Label, SessionLapView):
    pass
    
class SessionBrowser(object):
    def append_session(self, session):
        pass

    

