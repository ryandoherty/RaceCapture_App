import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from utils import kvFind
from kivy.properties import ObjectProperty
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle
from autosportlabs.widgets.scrollcontainer import ScrollContainer

Builder.load_file('autosportlabs/racecapture/views/dashboard/rawchannelview.kv')

NO_DATA_MSG = 'No Data'
DATA_MSG = ''

RAW_GRID_BGCOLOR_1 = [0  , 0  , 0  , 1.0]
RAW_GRID_BGCOLOR_2 = [0.1, 0.1, 0.1, 1.0]
RAW_NORMAL_COLOR = [0.0, 1.0, 0.0, 1.0]

class RawGauge(DigitalGauge):
    backgroundColor = ObjectProperty(RAW_GRID_BGCOLOR_1)

    def __init__(self, **kwargs):
        super(RawGauge  , self).__init__(**kwargs)
        self.normal_color = RAW_NORMAL_COLOR

    def update_colors(self):
        color = self.select_alert_color()
        self.valueView.color = color

class RawChannelView(Screen):
    _gauges = {}
    _grid = None
    _bgCurrent = RAW_GRID_BGCOLOR_1
    _databus = None
    settings = None

    def __init__(self, databus, settings, **kwargs):
        super(RawChannelView, self).__init__(**kwargs)
        self._databus = databus
        self.settings = settings
        self.initScreen()

    @property
    def _gridView(self):
        if self._grid == None:
            self._grid = kvFind(self, 'rcid', 'grid')
        return self._grid

    def on_meta(self, channel_metas):
        self._clearGauges()
        with channel_metas as cm:
            for channel_meta in cm.itervalues():
                self._addGauge(channel_meta)

    def initScreen(self):
        dataBus = self._databus
        dataBus.addMetaListener(self.on_meta)
        meta = self._databus.getMeta()

        if len(meta) > 0:
            self.on_meta(meta)

    def _enableNoDataStatus(self, enabled):
        statusView = kvFind(self, 'rcid', 'statusMsg')
        statusView.text = NO_DATA_MSG if enabled else DATA_MSG

    def _clearGauges(self):
        gridView = self._gridView
        gridView.clear_widgets()
        self._enableNoDataStatus(True)

    def _addGauge(self, channelMeta):
        channel = channelMeta.name
        gauge = RawGauge(rcid=None, dataBus=self._databus, settings=self.settings, targetchannel=channel)
        gridView = self._gridView
        gauge.precision = channelMeta.precision

        if len(gridView.children) % 3 == 0:
            self._bgCurrent = RAW_GRID_BGCOLOR_2 if self._bgCurrent == RAW_GRID_BGCOLOR_1 else RAW_GRID_BGCOLOR_1

        gauge.backgroundColor = self._bgCurrent
        gridView.add_widget(gauge)
        self._gauges[channel] = gauge
        self._enableNoDataStatus(False)
