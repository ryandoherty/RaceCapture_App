import kivy
kivy.require('1.9.1')
from fieldlabel import FieldLabel
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.anchorlayout import AnchorLayout
from utils import kvFind, kvFindClass
from kivy.metrics import dp
from autosportlabs.racecapture.views.dashboard.widgets.roundgauge import RoundGauge
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen

GAUGE_VIEW_KV = """
<GaugeView>:
    AnchorLayout:

        AnchorLayout:
            anchor_x:'left'
            anchor_y:'top'
            RoundGauge:
                size_hint_x: 0.3
                size_hint_y: 0.5
                rcid: 'tl'

        AnchorLayout:
            anchor_x:'left'
            anchor_y:'bottom'
            RoundGauge:
                size_hint_x: 0.3
                size_hint_y: 0.5
                rcid: 'bl'
        
        AnchorLayout:
            anchor_x:'right'
            anchor_y:'top'
            RoundGauge:
                size_hint_x: 0.3
                size_hint_y: 0.5
                rcid: 'tr'

        AnchorLayout:
            anchor_x:'right'
            anchor_y:'bottom'
            RoundGauge:
                size_hint_x: 0.3
                size_hint_y: 0.5
                rcid: 'br'                    
                    
        AnchorLayout:
            anchor_x:'center'
            anchor_y:'center'
            BoxLayout:
                size_hint_x: 0.47
                orientation: 'vertical'
                RoundGauge:
                    rcid: 'center'
"""

class GaugeView(DashboardScreen):

    Builder.load_string(GAUGE_VIEW_KV)

    def __init__(self, databus, settings, **kwargs):
        super(GaugeView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self._initialized = False

    def on_meta(self, channelMetas):
        gauges = self._find_active_gauges()

        for gauge in gauges:
            channel = gauge.channel
            if channel:
                channelMeta = channelMetas.get(channel)
                if channelMeta:
                    gauge.precision = channelMeta.precision
                    gauge.min = channelMeta.min
                    gauge.max = channelMeta.max

    def _find_active_gauges(self):
        return list(kvFindClass(self, Gauge))

    def on_enter(self):
        if not self._initialized:
            self._init_view()

    def _init_view(self):
        dataBus = self._databus
        dataBus.addMetaListener(self.on_meta)

        gauges = self._find_active_gauges()
        for gauge in gauges:
            gauge.settings = self._settings
            gauge.data_bus = dataBus
            channel = self._settings.userPrefs.get_gauge_config(gauge.rcid)
            if channel:
                gauge.channel = channel

        self._initialized = True
