import kivy
kivy.require('1.8.0')
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from pygments.formatters.bbcode import BBCodeFormatter #explicit import to make pyinstaller work. do not remove
from kivy.uix.codeinput import CodeInput
from pygments.lexers import PythonLexer
from kivy.app import Builder
from kivy.extras.highlight import KivyLexer
from pygments import lexers
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from iconbutton import IconButton
from settingsview import SettingsMappedSpinner

SCRIPT_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/scriptview.kv'

LOGFILE_POLL_INTERVAL = 1
LOGWINDOW_MAX_LENGTH = 20000
        
class LogLevelSpinner(SettingsMappedSpinner):
    def __init__(self, **kwargs):    
        super(LogLevelSpinner, self).__init__(**kwargs)
        self.setValueMap({3: 'Error', 6: 'Info', 7:'Debug', 8:'Trace'}, 6)
        self.text = 'Info'

class LuaScriptingView(BaseConfigView):
    scriptCfg = None
    logfileView = None
    logfileScrollView = None
    script_view = None
    def __init__(self, **kwargs):
        Builder.load_file(SCRIPT_VIEW_KV)
        super(LuaScriptingView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.register_event_type('on_run_script')
        self.register_event_type('on_poll_logfile')
        self.register_event_type('on_logfile')
        self.register_event_type('on_set_logfile_level')
        self.logfileView = kvFind(self, 'rcid', 'logfile')
        self.script_view = kvFind(self, 'rcid', 'script')
        self.logfileScrollView = kvFind(self, 'rcid', 'logfileSv') 

    def on_loglevel_selected(self, instance, value):
        self.dispatch('on_set_logfile_level', value)
        
    def on_config_updated(self, rcpCfg):
        scriptCfg = rcpCfg.scriptConfig
        self.script_view.text = scriptCfg.script
        self.scriptCfg = scriptCfg
   
    def on_script_changed(self, instance, value):
        if self.scriptCfg:
            self.scriptCfg.script = value
            self.scriptCfg.stale = True
            self.dispatch('on_modified')
            
    def on_run_script(self):
        pass
    
    def on_set_logfile_level(self, level):
        pass
    
    def on_poll_logfile(self):
        pass
        
    def on_logfile(self, value):
        current_text = self.logfileView.text
        current_text += str(value)
        overflow = len(current_text) - LOGWINDOW_MAX_LENGTH
        if overflow > 0:
            current_text = current_text[overflow:]
        self.logfileView.text = current_text        
        self.logfileScrollView.scroll_y = 0.0
    
    def clearLog(self):
        self.logfileView.text = ''
        
    def runScript(self):
        self.dispatch('on_run_script')
        
    def poll_logfile(self, dt):
        self.dispatch('on_poll_logfile')
        
    def enableScript(self, instance, value):
        if value:
            Clock.schedule_interval(self.poll_logfile, LOGFILE_POLL_INTERVAL)
        else:
            Clock.unschedule(self.poll_logfile)
        
        
class LuaCodeInput(CodeInput):
    def __init__(self, **kwargs):
        super(LuaCodeInput, self).__init__(**kwargs)
        self.lexer= lexers.get_lexer_by_name('lua')
        
                
