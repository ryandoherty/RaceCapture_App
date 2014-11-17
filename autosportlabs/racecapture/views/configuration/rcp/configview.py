import os
import traceback
import kivy
from time import sleep
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from utils import *
from copy import *
from kivy.metrics import dp
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy import platform
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
from channels import *

RCP_CONFIG_FILE_EXTENSION = '.rcp'

Builder.load_file('autosportlabs/racecapture/views/configuration/rcp/configview.kv')

class LinkedTreeViewLabel(TreeViewLabel):
    view = None

class ConfigView(Screen):
    #file save/load
    config = ObjectProperty(None)
    loaded = BooleanProperty(False)
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    writeStale = BooleanProperty(False)
    track_manager = ObjectProperty(None)
    
    #List of config views
    configViews = []
    content = None
    menu = None
    rc_config = None
    scriptView = None
    _settings = None    

    def __init__(self, **kwargs):
        super(ConfigView, self).__init__(**kwargs)

        self.rc_config = kwargs.get('rcpConfig', None)
        self.rc_api = kwargs.get('rc_api', None)
        self.dataBusPump = kwargs.get('dataBusPump', None)
        self._settings = kwargs.get('settings')        

        self.register_event_type('on_config_updated')
        self.register_event_type('on_channels_updated')
        self.register_event_type('on_config_written')
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_config_modified')
        self.register_event_type('on_read_config')
        self.register_event_type('on_write_config')
        self.register_event_type('on_run_script')
        self.register_event_type('on_poll_logfile')
        self.register_event_type('on_set_logfile_level')
        
        self.content = kvFind(self, 'rcid', 'content')

    def on_config_written(self, *args):
        self.writeStale = False
        
    def on_config_modified(self, *args):
        self.writeStale = True

    def update_system_channels(self, system_channels):
        for view in self.configViews:
            channelWidgets = list(kvquery(view, __class__=ChannelNameSpinner))
            for channelWidget in channelWidgets:
                channelWidget.dispatch('on_channels_updated', system_channels)
        
    def on_channels_updated(self, system_channels):
        self.update_system_channels(system_channels)
        
    def on_config_updated(self, config):
        self.config = config
            
    def on_tracks_manager(self, instance, value):
        self.update_tracks()
        
    def on_config(self, instance, value):
        self.update_config_views()
    
    def on_loaded(self, instance, value):
        self.update_config_views()
        self.update_tracks()
        
    def on_writeStale(self, instance, value):
        self.updateControls()

    def _reset_stale(self):
        self.writeStale = False
        
    def update_config_views(self):
        config = self.config
        if config and self.loaded:        
            for view in self.configViews:
                view.dispatch('on_config_updated', config)
        Clock.schedule_once(lambda dt: self._reset_stale())
                
    def on_enter(self):
        if not self.loaded:
            Clock.schedule_once(lambda dt: self.createConfigViews(),0.1)
        
    def createConfigViews(self):
        tree = kvFind(self, 'rcid', 'menu')
        
        def create_tree(text):
            return tree.add_node(LinkedTreeViewLabel(text=text, is_open=True, no_selection=True))
    
        def on_select_node(instance, value):
            # ensure that any keyboard is released
            try:
                self.content.get_parent_window().release_keyboard()
            except:
                pass
    
            try:
                self.content.clear_widgets()
                self.content.add_widget(value.view)
            except Exception, e:
                print e
            
        def attach_node(text, n, view):
            label = LinkedTreeViewLabel(text=text)
            
            label.view = view
            label.color_selected =   [1.0,0,0,0.6]
            self.configViews.append(view)
            view.bind(on_config_modified=self.on_config_modified)
            return tree.add_node(label, n)

        system_channels = self._settings.systemChannels

        defaultNode = attach_node('Race Track/Sectors', None, TrackConfigView(rcpComms=self.rc_api))
        attach_node('GPS', None, GPSChannelsView(rcpComms=self.rc_api))
        attach_node('Lap Statistics', None, LapStatsView())        
        attach_node('Analog Sensors', None, AnalogChannelsView(channels=system_channels))
        attach_node('Pulse/RPM Sensors', None, PulseChannelsView(channels=system_channels))
        attach_node('Digital In/Out', None, GPIOChannelsView(channels=system_channels))
        attach_node('Accelerometer/Gyro', None, ImuChannelsView())
        attach_node('Pulse/Analog Out', None, AnalogPulseOutputChannelsView(channels=system_channels))
        attach_node('CAN Bus', None, CANConfigView())
        attach_node('OBDII', None, OBD2ChannelsView(channels=system_channels))
        attach_node('Wireless', None, WirelessConfigView())
        attach_node('Telemetry', None, TelemetryConfigView())
        scriptView = LuaScriptingView()
        scriptView.bind(on_run_script=self.runScript)
        scriptView.bind(on_poll_logfile=self.pollLogfile)
        scriptView.bind(on_set_logfile_level=self.setLogFileLevel)
        attach_node('Scripting', None, scriptView)
        self.scriptView = scriptView
        if FIRMWARE_UPDATABLE:
            attach_node('Firmware', None, FirmwareUpdateView(dataBusPump=self.dataBusPump))
        
        tree.bind(selected_node=on_select_node)
        tree.select_node(defaultNode)
        
        self.update_system_channels(system_channels)
        self.loaded = True
        
    def updateControls(self):
        kvFind(self, 'rcid', 'writeconfig').disabled = not self.writeStale
        
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
    
    def on_run_script(self):
        pass
        
    def on_logfile(self, logfileJson):
        if self.scriptView:
            logfileText = logfileJson.get('logfile').replace('\r','').replace('\0','')
            self.scriptView.dispatch('on_logfile', logfileText)
        
    def runScript(self, instance):
        self.dispatch('on_run_script')

    def on_poll_logfile(self):
        pass

    def on_set_logfile_level(self, level):
        pass
    
    def setLogFileLevel(self, instance, level):
        self.dispatch('on_set_logfile_level', level)
        
    def pollLogfile(self, instance):
        self.dispatch('on_poll_logfile')
    
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
        
    def doOpenConfig(self):
        content = LoadDialog(ok=self.load, cancel=self.dismiss_popup, filters=['*' + RCP_CONFIG_FILE_EXTENSION])
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()        
    
    def saveConfig(self):
        if self.rc_config.loaded:
            content = SaveDialog(ok=self.save, cancel=self.dismiss_popup,filters=['*' + RCP_CONFIG_FILE_EXTENSION])
            self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
            self._popup.open()
        else:
            alertPopup('Warning', 'Please load or read a configuration before saving')
        
    def load(self, instance):
        self.dismiss_popup()
        try:
            selection = instance.selection
            filename = selection[0] if len(selection) else None
            if filename:
                with open(filename) as stream:
                    rcpConfigJsonString = stream.read()
                    self.rc_config.fromJsonString(rcpConfigJsonString)
                    self.dispatch('on_config_updated', self.rc_config)
                    self.on_config_modified()
            else:
                alertPopup('Error Loading', 'No config file selected')
        except Exception as detail:
            alertPopup('Error Loading', 'Failed to Load Configuration:\n\n' + str(detail))
            
    def save(self, instance):
        self.dismiss_popup()
        try:        
            filename = instance.filename
            if len(filename):
                filename = os.path.join(instance.path, filename)
                if not filename.endswith(RCP_CONFIG_FILE_EXTENSION): filename += RCP_CONFIG_FILE_EXTENSION
                with open(filename, 'w') as stream:
                    configJson = self.rc_config.toJsonString()
                    stream.write(configJson)
        except Exception as detail:
            alertPopup('Error Saving', 'Failed to save:\n\n' + str(detail))

    def dismiss_popup(self, *args):
        self._popup.dismiss()
                
