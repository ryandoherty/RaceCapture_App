import kivy
kivy.require('1.9.0')
from utils import *
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.app import Builder
from kivy.clock import Clock
from autosportlabs.uix.iconbutton import IconButton
from kivy.logger import Logger

Builder.load_file('toolbarview.kv')

TOOLBAR_LED_DURATION = 2.0
PROGRESS_COMPLETE_LINGER_DURATION = 5.0
ACTIVITY_MESSAGE_LINGER_DURATION = 10.0

class ToolbarView(BoxLayout):
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

    normalStatusColor = [0.8, 0.8, 0.8, 1.0]
    alertStatusColor = [1.0, 0.64, 0.0, 1.0]
    
    progressBar = None
    teleStatus = None
    rcTxStatus = None
    rcRxStatus = None

    def __init__(self, **kwargs):
        super(ToolbarView, self).__init__(**kwargs)
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
        
    def on_activity(self, msg):
        self.setActivityMessage(msg)
        self._activityDecay()
        
    def setActivityMessage(self, msg):
        activityLabel = kvFind(self, 'rcid', 'activity')
        activityLabel.text = msg
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    def on_status(self, msg, isAlert):
        statusLabel = kvFind(self, 'rcid', 'status')
        statusLabel.text = msg
        if isAlert == True:
            statusLabel.color = self.alertStatusColor
        else:
            statusLabel.color = self.normalStatusColor
            
    def update_progress(self, value):
        if not self.progressBar:
            self.progressBar = kvFind(self, 'rcid', 'pbar')
        self.progressBar.value = value
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
        
    def on_activity_decay(self, dt):
        self.setActivityMessage('')

    def on_rc_tx_decay(self, dt):
        self.on_rc_tx(False)
        
    def on_rc_tx(self, value):
        if not self.rcTxStatus:
            self.rcTxStatus = kvFind(self, 'rcid', 'rcTxStatus')            
        self.rcTxStatus.color = self.txOnColor if value else self.txOffColor
        self._rcTxDecay()
    
    def on_rc_rx_decay(self, dt):
        self.on_rc_rx(False)
        
    def on_rc_rx(self, value):
        if not self.rcRxStatus:
            self.rcRxStatus = kvFind(self, 'rcid', 'rcRxStatus')    
        self.rcRxStatus.color = self.rxOnColor if value else self.rxOffColor
        self._rcRxDecay()        

    def on_tele_status(self, status):
        if not self.teleStatus:
            self.teleStatus = kvFind(self, 'rcid', 'teleStatus')
        try:        
            self.teleStatus.color = self.telemetry_color[status]
        except:
            Logger.error("ToolbarView: Invalid telemetry status: " + str(status))

