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
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/dashboardview.kv')

class DashboardView(Screen):
    
    _settings = None
    _databus = None
    _screen_mgr = None
    _gaugeView = None
    _tachView = None
    _rawchannelView = None
    _laptimeView = None
    _comboView = None
    
    def __init__(self, **kwargs):
        super(DashboardView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self.init_view()
            
    def on_tracks_updated(self, trackmanager):
        pass
        
    def initGlobalGauges(self):
        dataBus = self._databus
        settings = self._settings
 
        activeGauges = list(kvFindClass(self, Gauge))
        
        for gauge in activeGauges:
            gauge.settings = settings
            gauge._data_bus = dataBus
         
    def init_view(self):
        screenMgr = kvFind(self, 'rcid', 'screens')
        
        dataBus = self._databus
        settings = self._settings
        
        self.initGlobalGauges()
        
        gaugeView = GaugeView(name='gaugeView', dataBus=dataBus, settings=settings)
        tachView = TachometerView(name='tachView', dataBus=dataBus, settings=settings)
        laptimeView = LaptimeView(name='laptimeView', dataBus=dataBus, settings=settings)
        comboView = ComboView(name='comboView', dataBus=dataBus, settings=settings)
        rawChannelView = RawChannelView(name='rawchannelView', dataBus=dataBus, settings=settings)
        
        #screenMgr.transition=WipeTransition()
        screenMgr.add_widget(gaugeView)
        screenMgr.add_widget(tachView)
        screenMgr.add_widget(laptimeView)
        screenMgr.add_widget(comboView)
        screenMgr.add_widget(rawChannelView)

        gauges = list(kvFindClass(self, DigitalGauge))

        for gauge in gauges:
            gauge.settings = self._settings
            gauge._data_bus = dataBus

        self._gaugeView = gaugeView
        self._tachView = tachView
        self._rawchannelView = rawChannelView
        self._laptimeView = laptimeView
        self._comboView = comboView
        self._screen_mgr = screenMgr

    def on_nav_left(self):
        self._screen_mgr.current = self._screen_mgr.previous()

    def on_nav_right(self):
        self._screen_mgr.current = self._screen_mgr.next()
        