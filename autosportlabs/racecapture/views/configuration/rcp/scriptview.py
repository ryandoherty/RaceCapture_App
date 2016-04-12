import kivy
kivy.require('1.9.1')
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from pygments.formatters.bbcode import BBCodeFormatter #explicit import to make pyinstaller work. do not remove
from kivy.uix.codeinput import CodeInput
from kivy.uix.textinput import TextInput
from pygments.lexers import PythonLexer
from kivy.app import Builder
from kivy.extras.highlight import KivyLexer
from pygments import lexers
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from iconbutton import IconButton, LabelIconButton
from settingsview import SettingsMappedSpinner
from autosportlabs.widgets.scrollcontainer import ScrollContainer

SCRIPT_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/scriptview.kv'

LOGFILE_POLL_INTERVAL = 1
LOGWINDOW_MAX_LENGTH = 1000
        
class LogLevelSpinner(SettingsMappedSpinner):
    def __init__(self, **kwargs):    
        super(LogLevelSpinner, self).__init__(**kwargs)
        self.setValueMap({3: 'Error', 6: 'Info', 7:'Debug', 8:'Trace'}, 6)
        self.text = 'Info'

class LuaScriptingView(BaseConfigView):

    def __init__(self, **kwargs):
        Builder.load_file(SCRIPT_VIEW_KV)
        super(LuaScriptingView, self).__init__(**kwargs)
        self.script_cfg = None
        self.register_event_type('on_config_updated')
        self.register_event_type('on_run_script')
        self.register_event_type('on_poll_logfile')
        self.register_event_type('on_logfile')
        self.register_event_type('on_set_logfile_level')

    def on_loglevel_selected(self, instance, value):
        self.dispatch('on_set_logfile_level', value)
        
    def on_config_updated(self, rcp_cfg):
        cfg = rcp_cfg.scriptConfig
        self.ids.lua_script.text = cfg.script
        self.script_cfg = cfg
   
    def on_script_changed(self, instance, value):
        if self.script_cfg:
            self.script_cfg.script = value
            self.script_cfg.stale = True
            self.dispatch('on_modified')
            
    def on_run_script(self):
        pass
    
    def on_set_logfile_level(self, level):
        pass
    
    def on_poll_logfile(self):
        pass
        
    def on_logfile(self, value):
        logfile_view = self.ids.logfile
        current_text = logfile_view.text
        current_text += str(value)
        overflow = len(current_text) - LOGWINDOW_MAX_LENGTH
        if overflow > 0:
            current_text = current_text[overflow:]
        logfile_view.text = current_text
        self.ids.logfile_sv.scroll_y = 0.0
    
    def clearLog(self):
        self.ids.logfile.text = ''
        
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
        
                
