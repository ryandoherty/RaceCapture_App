import kivy
from autosportlabs.racecapture.views.dashboard.tachometerview import TachometerView
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.screenmanager import *
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import Tachometer
from utils import kvFind
Builder.load_file('autosportlabs/racecapture/views/dashboard/dashboardview.kv')

class DashboardView(Screen):
    
    tachView = None
    
    def __init__(self, **kwargs):
        super(DashboardView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self.initView()
            
    def on_tracks_updated(self, trackManager):
        pass
        
    def initView(self):
        screenMgr = kvFind(self, 'rcid', 'screens')
        tachView = TachometerView(name='tachView')
        screenMgr.transition=NoTransition()
        
        screenMgr.add_widget(tachView)
        
        self.tachView = tachView
             