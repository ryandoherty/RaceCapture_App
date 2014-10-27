import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.uix.screenmanager import Screen

Builder.load_file('autosportlabs/racecapture/views/analysis/analysisview.kv')

class AnalysisView(Screen):
    _settings = None
    _databus = None
    
    def __init__(self, **kwargs):
        super(AnalysisView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self.init_view()
    
    def on_tracks_updated(self, trackManager):
        pass

    def init_view(self):
        pass