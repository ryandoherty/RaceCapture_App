#!/usr/bin/python
__version__ = "1.4.3"
import sys
import os

if __name__ == '__main__' and sys.platform == 'win32':
    from multiprocessing import freeze_support
    freeze_support()

if __name__ == '__main__':
    import logging
    import argparse
    import kivy
    import os
    import traceback
    from kivy.properties import AliasProperty
    from functools import partial
    from kivy.clock import Clock
    from kivy.config import Config
    from kivy.logger import Logger
    kivy.require('1.9.0')
    from kivy.base import ExceptionManager, ExceptionHandler
    Config.set('graphics', 'width', '1024')
    Config.set('graphics', 'height', '576')
    Config.set('kivy', 'exit_on_escape', 0)
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.popup import Popup
    from kivy.uix.screenmanager import *
    from utils import *
    from installfix_garden_navigationdrawer import NavigationDrawer
    from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup
    from autosportlabs.racecapture.views.tracks.tracksview import TracksView
    from autosportlabs.racecapture.views.configuration.rcp.configview import ConfigView
    from autosportlabs.racecapture.views.status.statusview import StatusView
    from autosportlabs.racecapture.views.dashboard.dashboardview import DashboardView
    from autosportlabs.racecapture.views.analysis.analysisview import AnalysisView
    from autosportlabs.racecapture.views.preferences.preferences import PreferencesView
    from autosportlabs.racecapture.menu.mainmenu import MainMenu
    from autosportlabs.comms.commsfactory import comms_factory
    from autosportlabs.racecapture.tracks.trackmanager import TrackManager
    from autosportlabs.racecapture.menu.homepageview import HomePageView
    from autosportlabs.racecapture.settings.systemsettings import SystemSettings
    from autosportlabs.racecapture.settings.prefs import Range
    from autosportlabs.telemetry.telemetryconnection import TelemetryManager
    from autosportlabs.help.helpmanager import HelpInfo
    from toolbarview import ToolbarView
    if not is_mobile_platform():
        kivy.config.Config.set ('input', 'mouse', 'mouse,multitouch_on_demand')

    # If we have a Sentry config file, create a client to send crash reports to
    if os.path.isfile('sentry.cfg'):
        import raven
        # .sentry file contains our Sentry DSN
        sentry_file = open('sentry.cfg', 'r')
        dsn = sentry_file.read().rstrip()
        sentry_client = raven.Client(dsn=dsn, release=__version__)

from kivy.app import App, Builder
from autosportlabs.racecapture.config.rcpconfig import RcpConfig, VersionConfig
from autosportlabs.racecapture.databus.databus import DataBusFactory, DataBusPump
from autosportlabs.racecapture.status.statuspump import StatusPump
from autosportlabs.racecapture.api.rcpapi import RcpApi

class RaceCaptureApp(App):

    # things that care about configuration being loaded
    config_listeners = []

    # things that care about tracks being loaded
    tracks_listeners = []

    # map of view keys to factory functions for building top level views
    view_builders = {}

    # container for all settings
    settings = None

    # Central RCP configuration object
    rc_config = RcpConfig()

    # dataBus provides an eventing / polling mechanism to parts of the system that care
    _databus = None

    # pumps data from rcApi to dataBus. kind of like a bridge
    _data_bus_pump = DataBusPump()

    _status_pump = StatusPump()

    # Track database manager
    trackManager = None

    # Application Status bars
    status_bar = None

    # main navigation menu
    mainNav = None

    # Main Screen Manager
    screenMgr = None

    # main view references for dispatching notifications
    mainViews = {}

    # application arguments - initialized upon startup
    app_args = []

    use_kivy_settings = False

    base_dir = None

    _telemetry_connection = None

    @staticmethod
    def get_app_version():
        return __version__

    def __init__(self, **kwargs):
        super(RaceCaptureApp, self).__init__(**kwargs)

        # We do this because when this app is bundled into a standalone app
        # by pyinstaller we must reference all files by their absolute paths
        # sys._MEIPASS is provided by pyinstaller
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # RaceCapture serial I/O
        self._rc_api = RcpApi(on_disconnect=self._on_rcp_disconnect)

        # self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        # self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.settings = SystemSettings(self.user_data_dir, base_dir=self.base_dir)
        self._databus = DataBusFactory().create_standard_databus(self.settings.systemChannels)
        self.settings.runtimeChannels.data_bus = self._databus
        HelpInfo.settings = self.settings

        Window.bind(on_keyboard=self._on_keyboard)
        self.register_event_type('on_tracks_updated')
        self.processArgs()
        self.settings.appConfig.setUserDir(self.user_data_dir)
        self.trackManager = TrackManager(user_dir=self.settings.get_default_data_dir(), base_dir=self.base_dir)
        self.setup_telemetry()

    def on_pause(self):
        return True

    def _on_keyboard(self, keyboard, keycode, *args):
        if keycode == 27:
            self.switchMainView('home')

    def processArgs(self):
        parser = argparse.ArgumentParser(description='Autosport Labs Race Capture App')
        parser.add_argument('-p', '--port', help='Port', required=False)
        parser.add_argument('--telemetryhost', help='Telemetry host', required=False)

        if sys.platform == 'win32':
            parser.add_argument('--multiprocessing-fork', required=False, action='store_true')

        self.app_args = vars(parser.parse_args())

    def getAppArg(self, name):
        return self.app_args.get(name, None)

    def first_time_setup(self):
        popup = None
        def _on_answer(instance, answer):
            popup.dismiss()
            if answer:
                self.showMainView('tracks')
                Clock.schedule_once(lambda dt: self.mainViews['tracks'].check_for_update(), 0.5)
        popup = confirmPopup('Race Tracks', 'Looks like this is your first time running.\n\nShould I update the Race Track database?', _on_answer)
        self.settings.userPrefs.set_pref('preferences', 'first_time_setup', False)

    def loadCurrentTracksSuccess(self):
        Logger.info('RaceCaptureApp: Current Tracks Loaded')
        Clock.schedule_once(lambda dt: self.notifyTracksUpdated())

    def loadCurrentTracksError(self, details):
        alertPopup('Error Loading Tracks', str(details))

    def init_data(self):
        self.trackManager.init(None, self.loadCurrentTracksSuccess, self.loadCurrentTracksError)

    def _serial_warning(self):
        alertPopup('Warning', 'Command failed. Ensure you have selected a correct serial port')

    # Logfile
    def on_poll_logfile(self, instance):
        try:
            self._rc_api.getLogfile()
        except:
            pass


    def on_set_logfile_level(self, instance, level):
        try:
            self._rc_api.setLogfileLevel(level, None, self.on_set_logfile_level_error)
        except:
            logging.exception('')
            self._serial_warning()

    def on_set_logfile_level_error(self, detail):
        alertPopup('Error', 'Error Setting Logfile Level:\n\n' + str(detail))

    # Run Script
    def on_run_script(self, instance):
        self._rc_api.runScript(self.on_run_script_complete, self.on_run_script_error)

    def on_run_script_complete(self, result):
        Logger.info('RaceCaptureApp: run script complete: ' + str(result))

    def on_run_script_error(self, detail):
        alertPopup('Error Running', 'Error Running Script:\n\n' + str(detail))

    # Write Configuration
    def on_write_config(self, instance, *args):
        rcpConfig = self.rc_config
        try:
            self._rc_api.writeRcpCfg(rcpConfig, self.on_write_config_complete, self.on_write_config_error)
            self.showActivity("Writing configuration")
        except:
            logging.exception('')
            self._serial_warning()

    def on_write_config_complete(self, result):
        Logger.info("RaceCaptureApp: Config written")
        self.showActivity("Writing completed")
        self.rc_config.stale = False
        self._data_bus_pump.meta_is_stale()
        for listener in self.config_listeners:
            Clock.schedule_once(lambda dt, inner_listener=listener: inner_listener.dispatch('on_config_written', self.rc_config))

    def on_write_config_error(self, detail):
        alertPopup('Error Writing', 'Could not write configuration:\n\n' + str(detail))

    # Read Configuration
    def on_read_config(self, instance, *args):
        try:
            self._rc_api.getRcpCfg(self.rc_config, self.on_read_config_complete, self.on_read_config_error)
            self.showActivity("Reading configuration")
        except:
            logging.exception('')
            self._serial_warning()

    def on_read_config_complete(self, rcpCfg):
        for listener in self.config_listeners:
            Clock.schedule_once(lambda dt, inner_listener=listener: inner_listener.dispatch('on_config_updated', self.rc_config))
        self.rc_config.stale = False

    def on_read_config_error(self, detail):
        alertPopup('Error Reading', 'Could not read configuration:\n\n' + str(detail))

    def on_tracks_updated(self, track_manager):
        for view in self.tracks_listeners:
            view.dispatch('on_tracks_updated', track_manager)

    def notifyTracksUpdated(self):
        self.dispatch('on_tracks_updated', self.trackManager)

    def on_main_menu_item(self, instance, value):
        self.switchMainView(value)

    def on_main_menu(self, instance, *args):
        self.mainNav.toggle_state()

    def showStatus(self, status, isAlert):
        self.status_bar.dispatch('on_status', status, isAlert)

    def showActivity(self, status):
        self.status_bar.dispatch('on_activity', status)

    def _setX(self, x):
        pass

    def _getX(self):
        pass

    def on_start(self):
        pass

    def on_stop(self):
        self._status_pump.stop()
        self._data_bus_pump.stop()
        self._rc_api.shutdown_api()
        self._telemetry_connection.telemetry_enabled = False

    def showMainView(self, view_name):
        try:
            view = self.mainViews.get(view_name)
            if not view:
                view = self.view_builders[view_name]()
                self.screenMgr.add_widget(view)
                self.mainViews[view_name] = view
            self.screenMgr.current = view_name
        except Exception as detail:
            Logger.error('RaceCaptureApp: Failed to load main view ' + str(view_name) + ' ' + str(detail))

    def switchMainView(self, view_name):
            self.mainNav.anim_to_state('closed')
            Clock.schedule_once(lambda dt: self.showMainView(view_name), 0.25)

    def build_config_view(self):
        config_view = ConfigView(name='config',
                                rcpConfig=self.rc_config,
                                rc_api=self._rc_api,
                                databus=self._databus,
                                settings=self.settings,
                                base_dir=self.base_dir,
                                track_manager=self.trackManager)
        config_view.bind(on_read_config=self.on_read_config)
        config_view.bind(on_write_config=self.on_write_config)
        config_view.bind(on_run_script=self.on_run_script)
        config_view.bind(on_poll_logfile=self.on_poll_logfile)
        config_view.bind(on_set_logfile_level=self.on_set_logfile_level)
        self._rc_api.addListener('logfile', lambda value: Clock.schedule_once(lambda dt: config_view.on_logfile(value)))
        self.config_listeners.append(config_view)
        self.tracks_listeners.append(config_view)
        return config_view

    def build_status_view(self):
        status_view = StatusView(self.trackManager, self._status_pump, name='status')
        self.tracks_listeners.append(status_view)
        return status_view

    def build_tracks_view(self):
        tracks_view = TracksView(name='tracks', track_manager=self.trackManager)
        self.tracks_listeners.append(tracks_view)
        return tracks_view

    def build_dash_view(self):
        dash_view = DashboardView(name='dash', dataBus=self._databus, settings=self.settings)
        self.tracks_listeners.append(dash_view)
        return dash_view

    def build_analysis_view(self):
        analysis_view = AnalysisView(name='analysis', data_bus=self._databus, settings=self.settings, track_manager=self.trackManager)
        self.tracks_listeners.append(analysis_view)
        return analysis_view

    def build_preferences_view(self):
        preferences_view = PreferencesView(name='preferences', settings=self.settings, base_dir=self.base_dir)
        preferences_view.settings_view.bind(on_config_change=self._on_preferences_change)
        return preferences_view

    def build_homepage_view(self):
        homepage_view = HomePageView(name='home')
        homepage_view.bind(on_select_view=lambda instance, view_name: self.switchMainView(view_name))
        return homepage_view

    def init_view_builders(self):
        self.view_builders = {'config': self.build_config_view,
                              'tracks': self.build_tracks_view,
                              'dash': self.build_dash_view,
                              'analysis': self.build_analysis_view,
                              'preferences': self.build_preferences_view,
                              'status': self.build_status_view,
                              'home': self.build_homepage_view
                              }

    def build(self):
        self.init_view_builders()

        Builder.load_file('racecapture.kv')
        root = self.root

        status_bar = root.ids.status_bar
        status_bar.bind(on_main_menu=self.on_main_menu)
        self.status_bar = status_bar

        root.ids.main_menu.bind(on_main_menu_item=self.on_main_menu_item)

        self.mainNav = root.ids.main_nav

        # reveal_below_anim
        # reveal_below_simple
        # slide_above_anim
        # slide_above_simple
        # fade_in
        self.mainNav.anim_type = 'slide_above_anim'

        rc_api = self._rc_api
        rc_api.on_progress = lambda value: status_bar.dispatch('on_progress', value)
        rc_api.on_rx = lambda value: status_bar.dispatch('on_rc_rx', value)
        rc_api.on_tx = lambda value: status_bar.dispatch('on_rc_tx', value)

        screenMgr = root.ids.main
        # NoTransition
        # SlideTransition
        # SwapTransition
        # FadeTransition
        # WipeTransition
        # FallOutTransition
        # RiseInTransition
        screenMgr.transition = NoTransition()

        self.screenMgr = screenMgr
        self.icon = ('resource/images/app_icon_128x128.ico' if sys.platform == 'win32' else 'resource/images/app_icon_128x128.png')
        Clock.schedule_once(lambda dt: self.post_launch(), 1.0)

    def post_launch(self):
        self._setup_toolbar()
        Clock.schedule_once(lambda dt: self.init_data())
        Clock.schedule_once(lambda dt: self.init_rc_comms())
        Clock.schedule_once(lambda dt: self.show_startup_view())

        #Ugly hack to handle track ids changing from strings to integers
        if self.settings.userPrefs.get_pref('preferences', 'integer_map_ids') == 'False' and self.settings.userPrefs.get_pref('preferences', 'first_time_setup') == 'False':
            Clock.schedule_once(lambda dt: self.refresh_tracks(), 0.5)

        self.check_first_time_setup()

    def refresh_tracks(self):
        popup = None
        def _on_answer(instance, answer):
            popup.dismiss()
            if answer:
                self.showMainView('tracks')
                self.trackManager.delete_all_local_tracks()
                self.settings.userPrefs.set_pref('preferences', 'integer_map_ids', True)
                Clock.schedule_once(lambda dt: self.mainViews['tracks'].check_for_update(), 0.5)
        popup = confirmPopup('Race Tracks', 'RaceCapture needs to refresh all tracks in order to properly configure RaceCapture/Pro.', _on_answer)

    def check_first_time_setup(self):
        if self.settings.userPrefs.get_pref('preferences', 'first_time_setup') == 'True':
            Clock.schedule_once(lambda dt: self.first_time_setup(), 0.5)

    def show_startup_view(self):
        settings_to_view = {'Home Page':'home',
                            'Dashboard':'dash',
                            'Analysis': 'analysis',
                            'Configuration': 'config' }
        view_pref = self.settings.userPrefs.get_pref('preferences', 'startup_screen')
        self.showMainView(settings_to_view[view_pref])

    def init_rc_comms(self):
        port = self.getAppArg('port')
        comms = comms_factory(port)
        rc_api = self._rc_api
        rc_api.detect_win_callback = self.rc_detect_win
        rc_api.detect_fail_callback = self.rc_detect_fail
        rc_api.detect_activity_callback = self.rc_detect_activity
        rc_api.init_api(comms)
        rc_api.run_auto_detect()

    def rc_detect_win(self, version):
        if version.is_compatible_version():
            self.showStatus("{} v{}.{}.{}".format(version.friendlyName, version.major, version.minor, version.bugfix), False)
            self._data_bus_pump.start(self._databus, self._rc_api)
            self._status_pump.start(self._rc_api)

            if self.settings.userPrefs.get_pref('preferences', 'send_telemetry') == "1" and self._telemetry_connection:
                self._telemetry_connection.telemetry_enabled = True

            if self.rc_config.loaded == False:
                Clock.schedule_once(lambda dt: self.on_read_config(self))
            else:
                self.showActivity('Connected')
        else:
            alertPopup('Incompatible Firmware', 'Detected {} v{}\n\nPlease upgrade firmware to {} or higher'.format(
                               version.friendlyName,
                               version.version_string(),
                               VersionConfig.get_minimum_version().version_string()
                               ))

    def rc_detect_fail(self):

        def re_detect():
            if not self._rc_api.comms.isOpen():
                self._rc_api.run_auto_detect()

        self.showStatus("Connecting...", True)
        Clock.schedule_once(lambda dt: re_detect(), 1.0)

    def rc_detect_activity(self, info):
        self.showActivity('Searching {}'.format(info))

    def _on_rcp_disconnect(self):
        if self._telemetry_connection.telemetry_enabled:
            self._telemetry_connection.telemetry_enabled = False

    def open_settings(self, *largs):
        self.switchMainView('preferences')

    def _setup_toolbar(self):
        status_bar = self.root.ids.status_bar
        status_bar.status_pump = self._status_pump
        status_bar.track_manager = self.trackManager

    def setup_telemetry(self):
        host = self.getAppArg('telemetryhost')

        telemetry_enabled = True if self.settings.userPrefs.get_pref('preferences', 'send_telemetry') == "1" else False

        self._telemetry_connection = TelemetryManager(self._databus, host=host, telemetry_enabled=telemetry_enabled)
        self.config_listeners.append(self._telemetry_connection)
        self._telemetry_connection.bind(on_connecting=self.telemetry_connecting)
        self._telemetry_connection.bind(on_connected=self.telemetry_connected)
        self._telemetry_connection.bind(on_disconnected=self.telemetry_disconnected)
        self._telemetry_connection.bind(on_streaming=self.telemetry_streaming)
        self._telemetry_connection.bind(on_error=self.telemetry_error)
        self._telemetry_connection.bind(on_auth_error=self.telemetry_auth_error)

    def telemetry_connecting(self, instance, msg):
        self.status_bar.dispatch('on_tele_status', ToolbarView.TELEMETRY_CONNECTING)
        self.showActivity(msg)

    def telemetry_connected(self, instance, msg):
        self.status_bar.dispatch('on_tele_status', ToolbarView.TELEMETRY_CONNECTING)
        self.showActivity(msg)

    def telemetry_disconnected(self, instance, msg):
        self.status_bar.dispatch('on_tele_status', ToolbarView.TELEMETRY_IDLE)
        self.showActivity(msg)

    def telemetry_streaming(self, instance, msg):
        self.status_bar.dispatch('on_tele_status', ToolbarView.TELEMETRY_ACTIVE)

    def telemetry_auth_error(self, instance, msg):
        self.status_bar.dispatch('on_tele_status', ToolbarView.TELEMETRY_ERROR)
        self.showActivity(msg)

    def telemetry_error(self, instance, msg):
        self.showActivity(msg)
        self.status_bar.dispatch('on_tele_status', ToolbarView.TELEMETRY_ERROR)

    def _on_preferences_change(self, menu, config, section, key, value):
        """Called any time the app preferences are changed
        """
        token = (section, key)

        if token == ('preferences', 'send_telemetry'):
            if value == "1":  # Boolean settings values are 1/0, not True/False
                if self.rc_config.connectivityConfig.cellConfig.cellEnabled:
                    alertPopup('Telemetry error', "Turn off RaceCapture's telemetry module for app to stream telemetry.")
                self._telemetry_connection.telemetry_enabled = True
            else:
                self._telemetry_connection.telemetry_enabled = False

if __name__ == '__main__':

    class CrashHandler(ExceptionHandler):
        def handle_exception(self, exception_info):
            if type(exception_info) == KeyboardInterrupt:
                Logger.info("CrashHander: KeyboardInterrupt")
                App.get_running_app().stop()
            Logger.critical("CrashHandler: Caught exception in Kivy loop: " + str(exception_info))
            Logger.critical(traceback.format_exc())
            if 'sentry_client' in globals():
                ident = sentry_client.captureException(value=exception_info)
                Logger.critical("CrashHandler: crash caught: Reference is %s" % ident)
            return ExceptionManager.PASS

    ExceptionManager.add_handler(CrashHandler())
    try:
        RaceCaptureApp().run()
    except:
        if 'sentry_client' in globals():
            ident = sentry_client.captureException()
            Logger.error("Main: crash caught: Reference is %s" % ident)
            traceback.print_exc()
        else:
            raise
