import kivy
kivy.require('1.9.0')
from utils import *
from kivy.properties import ObjectProperty, NumericProperty, ListProperty, StringProperty
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.progressbar import ProgressBar
from kivy.app import Builder
from kivy.clock import Clock
from iconbutton import IconButton
from kivy.logger import Logger
from fieldlabel import FieldLabel
from autosportlabs.racecapture.theme.color import ColorScheme
Builder.load_file('toolbarview.kv')

TOOLBAR_LED_DURATION = 2.0
PROGRESS_COMPLETE_LINGER_DURATION = 7.0
ACTIVITY_MESSAGE_LINGER_DURATION = 7.5

class ToolbarItem(BoxLayout):
    pass

class ProgressFieldLabel(AnchorLayout):
    minval = NumericProperty(0)
    maxval = NumericProperty(100)
    value = NumericProperty(0)
    color = ColorScheme.get_accent()
    text_color = ColorScheme.get_light_primary_text()
    text = StringProperty('')

    def __init__(self, **kwargs):
        super(ProgressFieldLabel, self).__init__(**kwargs)

    def on_minval(self, instance, value):
        self._refresh_value()

    def on_maxval(self, instance, value):
        self._refresh_value()

    def on_value(self, instance, value):
        self._refresh_value()

    def on_text(self, instance, value):
        self.ids.value.text = str(value)

    def _refresh_value(self):
        stencil = self.ids.stencil
        value = self.value
        minval = self.minval
        maxval = self.maxval
        pct = ((value - minval) / (maxval - minval))
        width = self.width * pct
        stencil.width = width

class ToolbarView(BoxLayout):
    status_pump = ObjectProperty(None)
    track_manager = ObjectProperty(None)

    TELEMETRY_IDLE = 0
    TELEMETRY_ACTIVE = 1
    TELEMETRY_CONNECTING = 2
    TELEMETRY_ERROR = 3
    
    telemetry_color = {TELEMETRY_IDLE:[0.0, 1.0, 0.0, 0.2],
                       TELEMETRY_ACTIVE:[0.0, 1.0, 0.0, 1.0],
                       TELEMETRY_CONNECTING:[1.0, 1.0, 0.0, 1.0],
                       TELEMETRY_ERROR:[1.0, 0.0, 0.0, 1.0]
                       }
    txOffColor = [0.0, 1.0, 0.0, 0.2]
    rxOffColor = [0.0, 0.8, 1.0, 0.2]
    txOnColor = [0.0, 1.0, 0.0, 1.0]
    rxOnColor = [0.0, 0.8, 1.0, 1.0]

    normalStatusColor = ColorScheme.get_light_primary_text()
    alertStatusColor = ColorScheme.get_alert()
    
    teleStatus = None
    rcTxStatus = None
    rcRxStatus = None

    def __init__(self, **kwargs):
        super(ToolbarView, self).__init__(**kwargs)
        self.current_status = ''
        self.register_event_type('on_main_menu')
        self.register_event_type('on_progress')
        self.register_event_type('on_rc_tx')
        self.register_event_type('on_rc_rx')
        self.register_event_type('on_tele_status')
        self.register_event_type('on_status')
        self.register_event_type('on_activity')
        
        self._rcTxDecay = Clock.create_trigger(self.on_rc_tx_decay, TOOLBAR_LED_DURATION)
        self._rcRxDecay = Clock.create_trigger(self.on_rc_rx_decay, TOOLBAR_LED_DURATION)                
        self._activityDecay = Clock.create_trigger(self.on_activity_decay, ACTIVITY_MESSAGE_LINGER_DURATION)
        self._progressDecay = Clock.create_trigger(self.on_progress_decay, PROGRESS_COMPLETE_LINGER_DURATION)
        
    def on_status_pump(self, instance, value):
        value.add_listener(self.on_rc_status_updated)

    def on_rc_status_updated(self, status_data):
        self._update_track_status(status_data)

    def on_activity(self, msg):
        self.setActivityMessage(msg)
        self._activityDecay()
        
    def set_state_message(self, msg):
        self.ids.state.text = msg

    def setActivityMessage(self, msg):
        prog_status = self.ids.prog_status
        prog_status.text = msg
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    def on_status(self, msg, isAlert):
        statusLabel = self.ids.prog_status
        statusLabel.text = msg
        self.current_status = msg
        if isAlert == True:
            statusLabel.text_color = self.alertStatusColor
        else:
            statusLabel.text_color = self.normalStatusColor
            
    def update_progress(self, value):
        self.ids.prog_status.value = value
        if value == 100:
            self._progressDecay()
        
    def on_progress(self, value):
        self.update_progress(value)
        
    def on_main_menu(self, instance, *args):
        pass
        
    def mainMenu(self):
        self.dispatch('on_main_menu', None)
    
    def on_progress_decay(self, dt):
        self.update_progress(0)
        self.ids.prog_status.text = self.current_status
        
    def on_activity_decay(self, dt):
        self.setActivityMessage(self.current_status)

    def on_rc_tx_decay(self, dt):
        self.on_rc_tx(False)
        
    def on_rc_tx(self, value):
        if not self.rcTxStatus:
            self.rcTxStatus = self.ids.rcTxStatus
        self.rcTxStatus.color = self.txOnColor if value else self.txOffColor
        self._rcTxDecay()
    
    def on_rc_rx_decay(self, dt):
        self.on_rc_rx(False)
        
    def on_rc_rx(self, value):
        if not self.rcRxStatus:
            self.rcRxStatus = self.ids.rcRxStatus
        self.rcRxStatus.color = self.rxOnColor if value else self.rxOffColor
        self._rcRxDecay()

    def on_tele_status(self, status):
        if not self.teleStatus:
            self.teleStatus = self.ids.teleStatus
        try:        
            self.teleStatus.color = self.telemetry_color[status]
        except:
            Logger.error("ToolbarView: Invalid telemetry status: " + str(status))

    def _update_track_status(self, status_data):
        try:
            track_status = status_data['status']['track']
            detection_status = track_status['status']
            if detection_status == 0:
                track_status_msg = 'Searching for Track'
            elif detection_status == 1:
                track_status_msg = 'User defined Track'
            else:
                if track_status['trackId'] != 0:
                    track = self.track_manager.find_track_by_short_id(track_status['trackId'])
                    if track is None:
                        track_status_msg = '(Unknown Track)'
                    else:
                        track_status_msg = track.name
                        configuration_name = track.configuration
                        if configuration_name and len(configuration_name):
                            track_status_msg += ' (' + configuration_name + ')'
                else:
                    track_status_msg = 'No track detected'
            self.set_state_message(track_status_msg)
        except Exception as e:
            Logger.warn("ToolbarView: Could not retrieve track detection status " + str(e))

