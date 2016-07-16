import kivy
kivy.require('1.9.1')
from fieldlabel import FieldLabel
from kivy.app import Builder
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
from autosportlabs.racecapture.views.dashboard.widgets.gauge import SingleChannelGauge, Gauge
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen

LAPTIME_VIEW_KV = """
<LaptimeView>:
    BoxLayout:
        orientation: 'vertical'
        CurrentLaptime:
            size_hint_y: 0.3
            rcid: 'curLap'
            halign: 'center'
            normal_color: [1.0, 1.0 , 1.0, 1.0]
        BoxLayout:
            size_hint_y: 0.55
            orientation: 'horizontal'
            AnchorLayout:
                size_hint_x: 0.25
                BigNumberView:
                    rcid: 'bignumberview_laptime'
                    size_hint: (0.8, 0.8)
                    channel: 'CurrentLap'
                    warning_color: [0.2, 0.2, 0.2, 1.0]
                    alert_color: [0.2, 0.2, 0.2, 1.0]
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.65
                BoxLayout:
                    size_hint_y: 0.1
                TimeDelta:
                    size_hint_y: 0.8
                    rcid: 'delta'
                    channel: 'LapDelta'
                    halign: 'right'
                    valign: 'middle'
                BoxLayout:
                    size_hint_y: 0.1
            BoxLayout:
                size_hint_x: 0.1
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.15
            spacing: self.height * 0.1
            FieldLabel:
                size_hint_x: 0.15
                font_size: self.height * 0.5
                halign: 'right'
                text: 'Best'
            Laptime:
                rcid: 'bestLap'
                channel: 'BestLap'
                size_hint_x: 0.35
                halign: 'left'
                normal_color: [1.0, 0.0 , 1.0, 1.0]
            Laptime:
                rcid: 'sector'
                channel: 'SectorTime'
                size_hint_x: 0.35
                halign: 'right'
                normal_color: [1.0, 1.0 , 0.0, 1.0]
            FieldLabel:
                size_hint_x: 0.15
                font_size: self.height * 0.5
                halign: 'left'
                rcid: 'sector'
                text: 'Sector'
"""

class LaptimeView(DashboardScreen):
    Builder.load_string(LAPTIME_VIEW_KV)

    _databus = None
    _settings = None

    def __init__(self, databus, settings, **kwargs):
        super(LaptimeView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self._initialized = False

    def on_meta(self, channelMetas):
        gauges = self.findActiveGauges(SingleChannelGauge)

        for gauge in gauges:
            channel = gauge.channel
            if channel:
                channelMeta = channelMetas.get(channel)
                if channelMeta:
                    gauge.precision = channelMeta.precision
                    gauge.min = channelMeta.min
                    gauge.max = channelMeta.max

    def findActiveGauges(self, gauge_type):
        return list(kvFindClass(self, gauge_type))

    def on_enter(self):
        if not self._initialized:
            self._init_screen()

    def _init_screen(self):
        dataBus = self._databus
        settings = self._settings
        dataBus.addMetaListener(self.on_meta)

        gauges = self.findActiveGauges(Gauge)
        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = dataBus

        self._initialized = True


