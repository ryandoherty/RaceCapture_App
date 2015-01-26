import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewNode

Builder.load_file('autosportlabs/racecapture/views/analysis/sessionbrowser.kv')

class SessionLapView(BoxLayout):
    def __init__(self, **kwargs):
        super(SessionLapView, self).__init__(**kwargs)
        lap = kwargs.get('lap','')
        laptime = kwargs.get('laptime', '---')
        
        self.ids.lap.text = str(lap)
        self.ids.laptime.text = str(laptime)
    
class TreeSessionLapView(SessionLapView, TreeViewNode):
    pass
    
class SessionBrowser(BoxLayout):
    
    def __init__(self, **kwargs):
        super(SessionBrowser, self).__init__(**kwargs)
    
    
    def append_lap(self, lapnumber, laptime):
        sessions = self.ids.sessions
        
        node = TreeSessionLapView(lap=lapnumber, laptime=laptime)
        sessions.add_node(node, None)

    

