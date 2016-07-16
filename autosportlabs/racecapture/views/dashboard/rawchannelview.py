import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.clock import Clock
from utils import kvFind
from kivy.properties import ObjectProperty
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen

RAW_GAUGE_KV = """
<RawGauge>:
    canvas.before:
        Color:
            rgba: self.backgroundColor
        Rectangle:
            pos: self.pos
            size: self.size
            
    is_removable: False
    is_channel_selectable: False
"""

class RawGauge(DigitalGauge):
    RAW_GRID_BGCOLOR_1 = [0  , 0  , 0  , 1.0]
    RAW_GRID_BGCOLOR_2 = [0.1, 0.1, 0.1, 1.0]
    RAW_NORMAL_COLOR = [0.0, 1.0, 0.0, 1.0]

    backgroundColor = ObjectProperty(RAW_GRID_BGCOLOR_1)
    Builder.load_string(RAW_GAUGE_KV)

    def __init__(self, **kwargs):
        super(RawGauge  , self).__init__(**kwargs)
        self.normal_color = RawGauge.RAW_NORMAL_COLOR

    def update_colors(self):
        color = self.select_alert_color()
        self.valueView.color = color

RAW_CHANNELS_VIEW_KV = """
<RawChannelView>:
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        FieldLabel:
            rcid: 'statusMsg'
            text: 'Waiting for Data'
            font_size: self.height * 0.1
            halign: 'center'
        ScrollContainer:
            id: scrlChan
            size_hint_y: 1.0
            do_scroll_x:False
            do_scroll_y:True
            GridLayout:
                id: grid
                padding: [self.height * 0.02, self.height * 0.02]
                row_default_height: root.height * 0.1
                size_hint_y: None
                height: self.minimum_height
                cols: 3            

"""

class RawChannelView(DashboardScreen):
    Builder.load_string(RAW_CHANNELS_VIEW_KV)
    NO_DATA_MSG = 'No Data'
    DATA_MSG = ''

    def __init__(self, databus, settings, **kwargs):
        super(RawChannelView, self).__init__(**kwargs)
        self._gauges = {}
        self._bgCurrent = RawGauge.RAW_GRID_BGCOLOR_1
        self._databus = databus
        self._settings = settings
        self._initialized = False

    def on_meta(self, channel_metas):
        if self._initialized == True:
            self._clear_gauges()
            for channel_meta in channel_metas.itervalues():
                self._add_gauge(channel_meta)

    def on_enter(self):
        if not self._initialized:
            self._init_screen()

    def _init_screen(self):
        dataBus = self._databus
        dataBus.addMetaListener(self.on_meta)
        meta = self._databus.getMeta()
        self._initialized = True

        if len(meta) > 0:
            self.on_meta(meta)

    def _enable_no_data_status(self, enabled):
        statusView = kvFind(self, 'rcid', 'statusMsg')
        statusView.text = RawChannelView.NO_DATA_MSG if enabled else RawChannelView.DATA_MSG

    def _clear_gauges(self):
        self.ids.grid.clear_widgets()
        self._enable_no_data_status(True)

    def _add_gauge(self, channelMeta):
        channel = channelMeta.name
        gauge = RawGauge(rcid=None, dataBus=self._databus, settings=self._settings, targetchannel=channel)
        grid = self.ids.grid
        gauge.precision = channelMeta.precision

        if len(grid.children) % 3 == 0:
            self._bgCurrent = RawGauge.RAW_GRID_BGCOLOR_2 if self._bgCurrent == RawGauge.RAW_GRID_BGCOLOR_1 else RawGauge.RAW_GRID_BGCOLOR_1

        gauge.backgroundColor = self._bgCurrent
        grid.add_widget(gauge)
        self._gauges[channel] = gauge
        self._enable_no_data_status(False)
