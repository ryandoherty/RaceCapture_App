import kivy
from valuefield import ValueField
kivy.require('1.9.1')

from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.switch import Switch
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from fieldlabel import FieldLabel
from autosportlabs.uix.textwidget import TextWidget
from helplabel import HelpLabel
from kivy.app import Builder
from utils import *
from mappedspinner import MappedSpinner
from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble, WarnLabel
from kivy.metrics import dp, sp

from kivy.properties import StringProperty

Builder.load_file('settingsview.kv')

class SettingsButton(Button):
    def __init__(self, **kwargs):
        super(SettingsButton, self).__init__(**kwargs)
        self.register_event_type('on_control')

    def on_control(self, value):
        pass

    def setValue(self, value):
        self.active = value
    
    def on_button_active(self, value):
        self.dispatch('on_control', value)

class SettingsSwitch(Switch):
    def __init__(self, **kwargs):
        super(SettingsSwitch, self).__init__(**kwargs)
        self.register_event_type('on_control')

    def on_control(self, value):
        pass

    def setValue(self, value):
        self.active = value
    
    def on_switch_active(self, value):
        self.dispatch('on_control', value)

class SettingsMappedSpinner(MappedSpinner):
    lastValue = None
    def __init__(self, **kwargs):
        super(SettingsMappedSpinner, self).__init__(**kwargs)
        self.register_event_type('on_control')

    def on_control(self, value):
        pass

    def setValue(self, value):
        self.setFromValue(value)
    
    def on_text(self, instance, value):
        if not value == self.lastValue: #eh.. prevent double firing of event. is there a better way?
            self.dispatch('on_control', instance.getValueFromKey(value))
            self.lastValue = value

class SettingsTextField(ValueField):
    def __init__(self, **kwargs):
        super(SettingsTextField, self).__init__(**kwargs)
        self.register_event_type('on_control')

    def on_control(self, value):
        pass

    def setValue(self, value):
        self.text = value
    
    def on_text(self, instance, value):
        self.dispatch('on_control', value)
    
    
    
class SettingsView(RelativeLayout):
    help_text = StringProperty('')
    label_text = StringProperty('')
    control = None
    rcid = StringProperty('')
    WARN_SHORT_TIMEOUT = 0.25
    WARN_LONG_TIMEOUT = 7.24

    def __init__(self, **kwargs):
        super(SettingsView, self).__init__(**kwargs)
        self.bind(help_text = self.on_help_text)
        self.bind(label_text = self.on_label_text)
        self.register_event_type('on_setting')     
        self.warn_bubble = None

    def on_setting(self, *args):
        pass
    
    def on_control(self, instance, value):
        self.dispatch('on_setting', value)
        pass

    def on_help_text(self, instance, value):
        help = kvFind(self, 'rcid', 'helpLabel')
        help.text = value

    def on_label_text(self, instance, value):
        label = kvFind(self, 'rcid', 'fieldLabel')
        label.text = value
        
    def setControl(self, widget):
        widget.size_hint_y=1.0
        kvFind(self, 'rcid', 'control').add_widget(widget)
        widget.bind(on_control=self.on_control)
        self.control = widget
            
    def setValue(self, value):
        if self.control:
            self.control.setValue(value)
    
    def set_error(self, error):
        if self.warn_bubble is None:
            warn = CenteredBubble()
            warn.add_widget(WarnLabel(text=str(error), font_size=sp(12)))
            warn.background_color = (1, 0, 0, 1.0)
            warn.auto_dismiss_timeout(self.WARN_LONG_TIMEOUT)
            control = kvFind(self, 'rcid', 'control')
            warn.size = (control.width, dp(50))
            warn.size_hint = (None, None)
            self.add_widget(warn)
            warn.center_below(control)
            self.warn_bubble = warn

    def clear_error(self):
        if self.warn_bubble is not None:
            self.warn_bubble.auto_dismiss_timeout(self.WARN_SHORT_TIMEOUT)
            self.warn_bubble = None
        
        
        

