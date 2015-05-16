import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewNode, TreeViewLabel
from kivy.metrics import dp
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef

Builder.load_file('autosportlabs/racecapture/views/analysis/sessionbrowser.kv')

class LapNode(BoxLayout):
    lap = 0
    session = 0
    def __init__(self, **kwargs):
        super(LapNode, self).__init__(**kwargs)
        self.register_event_type('on_lap_selected')
        lap = int(kwargs.get('lap'))
        session = int(kwargs.get('session'))
        laptime = kwargs.get('laptime')
        self.ids.lap.text = str(lap)
        self.ids.laptime.text = format_laptime(laptime)
        self.lap = lap
        self.session = session
        
    def on_lap_selected(self, *args):
        pass
    
    def lap_selected(self, instance, value):
        self.dispatch('on_lap_selected', SourceRef(self.lap, self.session), value)
        
        
class SessionNode(BoxLayout):
    def __init__(self, **kwargs):
        super(SessionNode, self).__init__(**kwargs)
        name = kwargs.get('name', '(unnamed)')
        notes = kwargs.get('notes', '')
        self.ids.name.text = self.notes = str(name)
        self.notes = str(notes)
        
class TreeLapNode(LapNode, TreeViewNode):
    pass
    
class TreeSessionNode(SessionNode, TreeViewNode):
    pass

class SessionBrowser(BoxLayout):
    
    def __init__(self, **kwargs):
        super(SessionBrowser, self).__init__(**kwargs)
        self.register_event_type('on_lap_selected')
    
    def append_session(self, name, notes):
        node = TreeSessionNode(name=name, notes=notes, height=dp(20))
        self.ids.sessions.add_node(node, None)
        return node
        
    def append_lap(self, session_node, session, lap, laptime):
        node = TreeLapNode(session=session, lap=lap, laptime=laptime, height=dp(20))
        node.bind(on_lap_selected=self.lap_selected)
        self.ids.sessions.add_node(node, session_node)
        return node

    def on_lap_selected(self, *args):
        pass
    
    def lap_selected(self, instance, source_ref, state):
        self.dispatch('on_lap_selected', source_ref, state)
        
    def clear_sessions(self):
        tree_view = self.ids.sessions
        nodes = []
        for node in tree_view.iterate_all_nodes(tree_view.get_root()):
            nodes.append(node)
            
        for node in nodes:
            tree_view.remove_node(node)
            

