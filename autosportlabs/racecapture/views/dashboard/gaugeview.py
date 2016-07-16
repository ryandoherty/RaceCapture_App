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

class GaugeView(DashboardScreen):

    def __init__(self, databus, settings, **kwargs):
        super(GaugeView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self._initialized = False

    def pct(self, p):
        return pct_h(p)

    def on_meta(self, channelMetas):
        gauges = self.findActiveGauges()

        for gauge in gauges:
            channel = gauge.channel
            if channel:
                channelMeta = channelMetas.get(channel)
                if channelMeta:
                    gauge.precision = channelMeta.precision
                    gauge.min = channelMeta.min
                    gauge.max = channelMeta.max

    def findActiveGauges(self):
        return list(kvFindClass(self, Gauge))

    def on_enter(self):
        if self._initialized == False:
            self._init_view()

    def _load_gauges(self):
        base = AnchorLayout()
        self.add_widget(base)

        top_left = AnchorLayout(anchor_x='left', anchor_y='top')
        top_left.add_widget(RoundGauge(size_hint_x=0.3, size_hint_y=0.5, rcid='tl'))
        base.add_widget(top_left)

        bottom_left = AnchorLayout(anchor_x='left', anchor_y='bottom')
        bottom_left.add_widget(RoundGauge(size_hint_x=0.3, size_hint_y=0.5, rcid='bl'))
        base.add_widget(bottom_left)

        top_right = AnchorLayout(anchor_x='right', anchor_y='top')
        top_right.add_widget(RoundGauge(size_hint_x=0.3, size_hint_y=0.5, rcid='tr'))
        base.add_widget(top_right)

        bottom_right = AnchorLayout(anchor_x='right', anchor_y='bottom')
        bottom_right.add_widget(RoundGauge(size_hint_x=0.3, size_hint_y=0.5, rcid='br'))
        base.add_widget(bottom_right)

        center = AnchorLayout(anchor_x='center', anchor_y='center')
        center.add_widget(RoundGauge(size_hint_x=0.47, rcid='center'))
        base.add_widget(center)


    def _init_view(self):
        self._load_gauges()
        dataBus = self._databus
        dataBus.addMetaListener(self.on_meta)

        gauges = self.findActiveGauges()
        for gauge in gauges:
            gauge.settings = self._settings
            gauge.data_bus = dataBus
            channel = self._settings.userPrefs.get_gauge_config(gauge.rcid)
            if channel:
                gauge.channel = channel

        self._initialized = True
