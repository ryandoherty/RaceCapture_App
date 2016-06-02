import kivy
kivy.require('1.9.1')
from autosportlabs.racecapture.views.dashboard.tachometerview import TachometerView
from autosportlabs.racecapture.views.dashboard.rawchannelview import RawChannelView
from autosportlabs.racecapture.views.dashboard.laptimeview import LaptimeView
from autosportlabs.racecapture.views.dashboard.comboview import ComboView
from autosportlabs.racecapture.views.dashboard.gaugeview import GaugeView
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
from autosportlabs.racecapture.views.dashboard.widgets.stopwatch import PitstopTimerView
from autosportlabs.racecapture.settings.systemsettings import SettingsListener
from kivy.uix.settings import SettingsWithNoMenu
from kivy.app import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import *
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import Tachometer
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
import os

DASHBOARD_VIEW_KV = 'autosportlabs/racecapture/views/dashboard/dashboardview.kv'
POPUP_DISMISS_TIMEOUT_LONG = 60.0


class DashboardView(Screen):
    _POPUP_SIZE_HINT = (0.75, 0.8)
    Builder.load_file(DASHBOARD_VIEW_KV)

    def __init__(self, **kwargs):
        _settings = None
        _databus = None
        _screen_mgr = None
        _gaugeView = None
        _tachView = None
        _rawchannelView = None
        _laptimeView = None
        _comboView = None
        super(DashboardView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self._alert_widgets = {}
        self.init_view()
        self._dismiss_popup_trigger = Clock.create_trigger(self._dismiss_popup, POPUP_DISMISS_TIMEOUT_LONG)
        self._popup = None
        

    def on_tracks_updated(self, trackmanager):
        pass

    def initGlobalGauges(self):
        databus = self._databus
        settings = self._settings

        activeGauges = list(kvFindClass(self, Gauge))

        for gauge in activeGauges:
            gauge.settings = settings
            gauge.data_bus = databus

    def init_view(self):
        screenMgr = kvFind(self, 'rcid', 'screens')

        databus = self._databus
        settings = self._settings

        self.initGlobalGauges()

        gaugeView = GaugeView(name='gaugeView', databus=databus, settings=settings)
        tachView = TachometerView(name='tachView', databus=databus, settings=settings)
        laptimeView = LaptimeView(name='laptimeView', databus=databus, settings=settings)
        # comboView = ComboView(name='comboView', databus=databus, settings=settings)
        rawChannelView = RawChannelView(name='rawchannelView', databus=databus, settings=settings)

        screenMgr.add_widget(gaugeView)
        screenMgr.add_widget(tachView)
        screenMgr.add_widget(laptimeView)
        # screenMgr.add_widget(comboView)
        screenMgr.add_widget(rawChannelView)

        gauges = list(kvFindClass(self, DigitalGauge))

        for gauge in gauges:
            gauge.settings = self._settings
            gauge.data_bus = databus

        self._gaugeView = gaugeView
        self._tachView = tachView
        self._rawchannelView = rawChannelView
        self._laptimeView = laptimeView
        # self._comboView = comboView
        self._screen_mgr = screenMgr

        self._alert_widgets['pit_stop'] = PitstopTimerView(databus, 'Pit Stop')

        databus.start_update()
        self._notify_preference_listeners()
        Clock.schedule_once(lambda dt: self._show_last_view())

    def on_enter(self):
        Window.bind(mouse_pos=self.on_mouse_pos)
        
    def on_leave(self):
        Window.unbind(mouse_pos=self.on_mouse_pos)
        
    def _got_activity(self):
        self.ids.preferences_button.brighten()
        
    def on_touch_down(self, touch):
        self._got_activity()
        return super(DashboardView, self).on_touch_down(touch)
    
    def on_mouse_pos(self, x, pos):
        if self.collide_point(pos[0], pos[1]):
            self._got_activity()
            self.ids.preferences_button.brighten()
        return False
    
    def on_preferences(self, *args):
        settings_view = SettingsWithNoMenu()
        base_dir = self._settings.base_dir
        settings_view.add_json_panel('Dashboard Preferences', self._settings.userPrefs.config, os.path.join(base_dir, 'resource', 'settings', 'dashboard_settings.json'))

        popup = ModalView(size_hint=self._POPUP_SIZE_HINT)
        popup.add_widget(settings_view)
        popup.bind(on_dismiss=self._popup_dismissed)
        popup.open()
        self._popup = popup
        # self._dismiss_popup_trigger()

    def _popup_dismissed(self, *args):
        self._notify_preference_listeners()

    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None

    def _notify_preference_listeners(self):
        listeners = list(kvFindClass(self, SettingsListener)) + self._alert_widgets.values()
        for listener in listeners:
            listener.user_preferences_updated(self._settings.userPrefs)

    def on_nav_left(self):
        self._screen_mgr.transition = SlideTransition(direction='right')
        self._show_screen(self._screen_mgr.previous())

    def on_nav_right(self):
        self._screen_mgr.transition = SlideTransition(direction='left')
        self._show_screen(self._screen_mgr.next())

    def _show_screen(self, screen):
        self._screen_mgr.current = screen
        self._settings.userPrefs.set_pref('preferences', 'last_dash_screen', screen)

    def _show_last_view(self):
        last_screen_name = self._settings.userPrefs.get_pref('preferences', 'last_dash_screen')
        self._screen_mgr.current = last_screen_name
