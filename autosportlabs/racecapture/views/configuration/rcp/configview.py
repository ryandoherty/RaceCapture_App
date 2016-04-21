import os
import traceback
import kivy
from time import sleep
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from utils import *
from copy import *
from kivy.metrics import dp, sp
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy import platform
from kivy.logger import Logger
from autosportlabs.widgets.scrollcontainer import ScrollContainer
FIRMWARE_UPDATABLE =  not (platform == 'android' or platform == 'ios')

from autosportlabs.racecapture.views.configuration.rcp.analogchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.imuchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.gpschannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.lapstatsview import *
from autosportlabs.racecapture.views.configuration.rcp.timerchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.gpiochannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.pwmchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.trackconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.obd2channelsview import *
from autosportlabs.racecapture.views.configuration.rcp.canconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.telemetryconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.wirelessconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.scriptview import *
if FIRMWARE_UPDATABLE:
    from autosportlabs.racecapture.views.configuration.rcp.firmwareupdateview import *
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.theme.color import ColorScheme

RCP_CONFIG_FILE_EXTENSION = '.rcp'

CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/configview.kv'

class LinkedTreeViewLabel(TreeViewLabel):
    view = None
    view_builder = None

class ConfigView(Screen):
    #file save/load
    loaded = BooleanProperty(False)
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    writeStale = BooleanProperty(False)
    track_manager = ObjectProperty(None)

    #List of config views
    configViews = []
    menu = None
    rc_config = None
    script_view = None
    _settings = None
    base_dir = None
    _databus = None
    
    def __init__(self, **kwargs):
        Builder.load_file(CONFIG_VIEW_KV)
        super(ConfigView, self).__init__(**kwargs)

        self._databus = kwargs.get('databus')
        self.rc_config = kwargs.get('rcpConfig', None)
        self.rc_api = kwargs.get('rc_api', None)
        self._settings = kwargs.get('settings')
        self.base_dir = kwargs.get('base_dir')

        self.register_event_type('on_config_updated')
        self.register_event_type('on_channels_updated')
        self.register_event_type('on_config_written')
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_config_modified')
        self.register_event_type('on_read_config')
        self.register_event_type('on_write_config')
        
    def on_config_written(self, *args):
        self.writeStale = False
        
    def on_config_modified(self, *args):
        self.writeStale = True

    def update_runtime_channels(self, system_channels):
        for view in self.configViews:
            channelWidgets = list(kvquery(view, __class__=ChannelNameSpinner))
            for channelWidget in channelWidgets:
                channelWidget.dispatch('on_channels_updated', system_channels)
        
    def on_channels_updated(self, runtime_channels):
        self.update_runtime_channels(runtime_channels)
        
    def on_config_updated(self, config):
        self.rc_config = config
        self.update_config_views()        
            
    def on_track_manager(self, instance, value):
        self.update_tracks()
            
    def on_loaded(self, instance, value):
        self.update_config_views()
        self.update_tracks()
        
    def on_writeStale(self, instance, value):
        self.updateControls()

    def _reset_stale(self):
        self.writeStale = False
        
    def update_config_views(self):
        config = self.rc_config
        if config and self.loaded:        
            for view in self.configViews:
                view.dispatch('on_config_updated', config)
        Clock.schedule_once(lambda dt: self._reset_stale())
                
    def init_screen(self):                
        self.createConfigViews()
        
    def on_enter(self):
        if not self.loaded:
            Clock.schedule_once(lambda dt: self.init_screen())
        
    def createConfigViews(self):
        tree = self.ids.menu
        
        def create_tree(text):
            return tree.add_node(LinkedTreeViewLabel(text=text, is_open=True, no_selection=True))
    
        def show_node(node):
            try:
                view = node.view
                if not view:
                    view = node.view_builder()
                    self.configViews.append(view)
                    view.bind(on_config_modified=self.on_config_modified)
                    node.view = view
                    if self.loaded:
                        if self.rc_config:
                            view.dispatch('on_config_updated', self.rc_config)
                        if self.track_manager:
                            view.dispatch('on_tracks_updated', self.track_manager)                                    
                Clock.schedule_once(lambda dt: self.ids.content.add_widget(view))

                
            except Exception as detail:
                alertPopup('Error', 'Error loading screen ' + str(node.text) + ':\n\n' + str(detail))
                Logger.error("ConfigView: Error selecting configuration view " + str(node.text))
            
        def on_select_node(instance, value):
            # ensure that any keyboard is released
            try:
                self.ids.content.get_parent_window().release_keyboard()
            except:
                pass
            self.ids.content.clear_widgets()
            Clock.schedule_once(lambda dt: show_node(value))
            
        def attach_node(text, n, view_builder):
            label = LinkedTreeViewLabel(text=text)
            label.view_builder = view_builder
            label.color_selected = ColorScheme.get_dark_primary()
            return tree.add_node(label, n)

        def create_scripting_view():
            script_view = LuaScriptingView(rc_api=self.rc_api)
            self.script_view = script_view
            return script_view            
            
        runtime_channels = self._settings.runtimeChannels

        defaultNode = attach_node('Race Tracks', None, lambda: TrackConfigView(databus=self._databus))
        attach_node('GPS', None, lambda: GPSChannelsView())
        attach_node('Race Timing', None, lambda: LapStatsView())        
        attach_node('Analog Sensors', None, lambda: AnalogChannelsView(channels=runtime_channels))
        attach_node('Pulse/RPM Sensors', None, lambda: PulseChannelsView(channels=runtime_channels))
        attach_node('Digital In/Out', None, lambda: GPIOChannelsView(channels=runtime_channels))
        attach_node('Accel/Gyro', None, lambda: ImuChannelsView(rc_api=self.rc_api))
        attach_node('Pulse/Analog Out', None, lambda: AnalogPulseOutputChannelsView(channels=runtime_channels))
        attach_node('CAN Bus', None, lambda: CANConfigView())
        attach_node('OBDII', None, lambda: OBD2ChannelsView(channels=runtime_channels, base_dir=self.base_dir))
        attach_node('Wireless', None, lambda: WirelessConfigView(base_dir=self.base_dir))
        attach_node('Telemetry', None, lambda: TelemetryConfigView())
        attach_node('Scripting', None, lambda: create_scripting_view())
        if FIRMWARE_UPDATABLE:
            attach_node('Firmware', None, lambda: FirmwareUpdateView(rc_api=self.rc_api, settings=self._settings))
        
        tree.bind(selected_node=on_select_node)
        tree.select_node(defaultNode)
        
        self.update_runtime_channels(runtime_channels)
        self.update_tracks()
        self.loaded = True
        
    def updateControls(self):
        Logger.debug("ConfigView: data is stale: " + str(self.writeStale))
        self.ids.write.disabled = not self.writeStale
        
    def update_tracks(self):
        track_manager = self.track_manager
        if track_manager and self.loaded:
            for view in self.configViews:
                view.dispatch('on_tracks_updated', track_manager)
        
    def on_tracks_updated(self, track_manager):
        self.track_manager = track_manager
    
    def on_read_config(self, instance, *args):
        pass
    
    def on_write_config(self, instance, *args):
        pass
        
    def readConfig(self):
        if self.writeStale == True:
            popup = None 
            def _on_answer(instance, answer):
                if answer:
                    self.dispatch('on_read_config', None)
                popup.dismiss()
            popup = confirmPopup('Confirm', 'Configuration Modified  - Continue Loading?', _on_answer)
        else:
            self.dispatch('on_read_config', None)

    def writeConfig(self):
        if self.rc_config.loaded:
            self.dispatch('on_write_config', None)
        else:
            alertPopup('Warning', 'Please load or read a configuration before writing')

    def openConfig(self):
        if self.writeStale:
            popup = None 
            def _on_answer(instance, answer):
                if answer:
                    self.doOpenConfig()
                popup.dismiss()
            popup = confirmPopup('Confirm', 'Configuration Modified  - Open Configuration?', _on_answer)
        else:
            self.doOpenConfig()

    def set_config_file_path(self, path):
        self._settings.userPrefs.set_pref('preferences', 'config_file_dir', path)
        
    def get_config_file_path(self):
        return self._settings.userPrefs.get_pref('preferences', 'config_file_dir')
                
    def doOpenConfig(self):
        content = LoadDialog(ok=self.load, cancel=self.dismiss_popup, filters=['*' + RCP_CONFIG_FILE_EXTENSION], user_path=self.get_config_file_path())
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()        
    
    def saveConfig(self):
        if self.rc_config.loaded:
            content = SaveDialog(ok=self.save, cancel=self.dismiss_popup,filters=['*' + RCP_CONFIG_FILE_EXTENSION], user_path=self.get_config_file_path())
            self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
            self._popup.open()
        else:
            alertPopup('Warning', 'Please load or read a configuration before saving')
        
    def load(self, instance):
        self.set_config_file_path(instance.path)
        self.dismiss_popup()
        try:
            selection = instance.selection
            filename = selection[0] if len(selection) else None
            if filename:
                with open(filename) as stream:
                    rcpConfigJsonString = stream.read()
                    self.rc_config.fromJsonString(rcpConfigJsonString)
                    self.rc_config.stale = True
                    self.dispatch('on_config_updated', self.rc_config)
                    Clock.schedule_once(lambda dt: self.on_config_modified())
                    
            else:
                alertPopup('Error Loading', 'No config file selected')
        except Exception as detail:
            alertPopup('Error Loading', 'Failed to Load Configuration:\n\n' + str(detail))
            Logger.exception('ConfigView: Error loading config: ' + str(detail))
                        
    def save(self, instance):
        def _do_save_config(filename):
            if not filename.endswith(RCP_CONFIG_FILE_EXTENSION): filename += RCP_CONFIG_FILE_EXTENSION
            with open(filename, 'w') as stream:
                configJson = self.rc_config.toJsonString()
                stream.write(configJson)
        
        self.set_config_file_path(instance.path)        
        self.dismiss_popup()
        config_filename = instance.filename
        if len(config_filename):
            try:        
                config_filename = os.path.join(instance.path, config_filename)
                if os.path.isfile(config_filename):
                    def _on_answer(instance, answer):
                        if answer:
                            _do_save_config(config_filename)
                        popup.dismiss()
                    popup = confirmPopup('Confirm', 'File Exists - overwrite?', _on_answer)
                else:
                    _do_save_config(config_filename)
            except Exception as detail:
                alertPopup('Error Saving', 'Failed to save:\n\n' + str(detail))
                Logger.exception('ConfigView: Error Saving config: ' + str(detail))

    def dismiss_popup(self, *args):
        self._popup.dismiss()
                
