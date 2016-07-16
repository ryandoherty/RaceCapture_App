import kivy
kivy.require('1.9.1')
from autosportlabs.racecapture.views.dashboard.tachometerview import TachometerView
from autosportlabs.racecapture.views.dashboard.rawchannelview import RawChannelView
from autosportlabs.racecapture.views.dashboard.laptimeview import LaptimeView
from autosportlabs.racecapture.views.dashboard.comboview import ComboView
from autosportlabs.racecapture.views.dashboard.gaugeview import GaugeView
from kivy.uix.carousel import Carousel
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
from autosportlabs.racecapture.views.dashboard.widgets.stopwatch import PitstopTimerView
from autosportlabs.racecapture.settings.systemsettings import SettingsListener
from kivy.uix.settings import SettingsWithNoMenu
from kivy.app import Builder
from kivy.core.window import Window, Keyboard
from kivy.uix.screenmanager import *
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import TachometerGauge
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
import os
from collections import OrderedDict

DASHBOARD_VIEW_KV = 'autosportlabs/racecapture/views/dashboard/dashboardview.kv'
POPUP_DISMISS_TIMEOUT_LONG = 60.0


class DashboardView(Screen):
    _POPUP_SIZE_HINT = (0.75, 0.8)
    Builder.load_file(DASHBOARD_VIEW_KV)

    def __init__(self, **kwargs):
        self._screen_mgr = None
        self._screens = OrderedDict()
        super(DashboardView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self._alert_widgets = {}
        self._initialized = False
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

    def _add_screen(self, screen):
        self._screens[screen.name] = screen
        screenMgr = kvFind(self, 'rcid', 'screens')
        screenMgr.add_widget(screen)

    def init_view(self):
        screenMgr = kvFind(self, 'rcid', 'screens')

        databus = self._databus
        settings = self._settings

        self.initGlobalGauges()

        self._add_screen(GaugeView(name='gaugeView', databus=databus, settings=settings))
        self._add_screen(TachometerView(name='tachView', databus=databus, settings=settings))
        self._add_screen(LaptimeView(name='laptimeView', databus=databus, settings=settings))
        self._add_screen(RawChannelView(name='rawchannelView', databus=databus, settings=settings))

        gauges = list(kvFindClass(self, DigitalGauge))

        for gauge in gauges:
            gauge.settings = self._settings
            gauge.data_bus = databus

        self._screen_mgr = screenMgr

        self._alert_widgets['pit_stop'] = PitstopTimerView(databus, 'Pit Stop')

        databus.start_update()
        self._notify_preference_listeners()
        self._show_last_view()
        self._initialized = True

    def on_enter(self):
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_key_down=self.on_key_down)
        if not self._initialized:
            self.init_view()

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

    def on_key_down(self, window, key, *args):
        if key == Keyboard.keycodes['left']:
            self.on_nav_left()
        elif key == Keyboard.keycodes['right']:
            self.on_nav_right()
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
        self._screen_mgr.load_previous()

    def on_nav_right(self):
        self._screen_mgr.transition = SlideTransition(direction='left')
        self._screen_mgr.load_next()

    def on_current_slide(self, slide_screen):
        if self._initialized == True:
            slide_screen.on_enter()
            self._settings.userPrefs.set_pref('preferences', 'last_dash_screen', slide_screen.name)

    def _show_screen(self, screen_name):
        # Find the index of the screen based on the screen name
        # and use that to select the index of the carousel
        index = 0
        for screen in self._screens.values():
            if screen_name == screen.name:
                self._screen_mgr.index = index
                screen.on_enter()
                break
            index += 1

    def _show_last_view(self):
        last_screen_name = self._settings.userPrefs.get_pref('preferences', 'last_dash_screen')
        Clock.schedule_once(lambda dt: self._show_screen(last_screen_name), 1.0)
