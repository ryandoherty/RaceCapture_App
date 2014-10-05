import kivy
from autosportlabs.racecapture.views.dashboard.tachometerview import TachometerView
from autosportlabs.racecapture.views.dashboard.rawchannelview import RawChannelView
from autosportlabs.racecapture.views.dashboard.laptimeview import LaptimeView
from autosportlabs.racecapture.views.dashboard.comboview import ComboView
from autosportlabs.racecapture.views.dashboard.gaugeview import GaugeView
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.screenmanager import *
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import Tachometer
from utils import kvFind
Builder.load_file('autosportlabs/racecapture/views/dashboard/dashboardview.kv')

class DashboardView(Screen):
    
    _screenMgr = None
    _gaugeView = None
    _tachView = None
    _rawchannelView = None
    _laptimeView = None
    _comboView = None
    
    def __init__(self, **kwargs):
        super(DashboardView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self.initView()
            
    def on_tracks_updated(self, trackManager):
        pass
        
    def initView(self):
        screenMgr = kvFind(self, 'rcid', 'screens')
        
        gaugeView = GaugeView(name='gaugeView')
        tachView = TachometerView(name='tachView')
        laptimeView = LaptimeView(name='laptimeView')
        comboView = ComboView(name='comboView')
        rawChannelView = RawChannelView(name='rawchannelView')
        
        screenMgr.transition=WipeTransition()
        screenMgr.add_widget(rawChannelView)
        screenMgr.add_widget(tachView)
        screenMgr.add_widget(gaugeView)
        screenMgr.add_widget(laptimeView)
        screenMgr.add_widget(comboView)
        
        self._gaugeView = gaugeView
        self._tachView = tachView
        self._rawchannelView = rawChannelView
        self._laptimeView = laptimeView
        self._comboView = comboView
        
        self._screenMgr = screenMgr

    def on_nav_left(self):
        self._screenMgr.current = self._screenMgr.previous()

    def on_nav_right(self):
        self._screenMgr.current = self._screenMgr.next()
        