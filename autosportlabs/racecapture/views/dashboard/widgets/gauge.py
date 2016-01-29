import kivy
kivy.require('1.9.0')
from kivy.properties import ListProperty, StringProperty, NumericProperty, ObjectProperty, DictProperty,\
    BooleanProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.bubble import BubbleButton
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from utils import kvFind, kvquery, dist
from functools import partial
from kivy.app import Builder
from kivy.logger import Logger
from autosportlabs.racecapture.settings.prefs import Range
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from autosportlabs.racecapture.views.channels.channelcustomizationview import ChannelCustomizationView
from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble
from autosportlabs.racecapture.data.channels import *
from autosportlabs.racecapture.views.util.viewutils import format_laptime

DEFAULT_NORMAL_COLOR  = [1.0, 1.0 , 1.0, 1.0]

DEFAULT_VALUE = None
DEFAULT_MIN = 0
DEFAULT_MAX = 100
DEFAULT_PRECISION = 0
DEFAULT_TYPE = CHANNEL_TYPE_SENSOR
MENU_ITEM_RADIUS = 100
POPUP_DISMISS_TIMEOUT_SHORT = 10.0
POPUP_DISMISS_TIMEOUT_LONG = 60.0

Builder.load_string('''
<CustomizeGaugeBubble>
    orientation: 'vertical'
    size_hint: (None, None)
    #pos_hint: {'center_x': .5, 'y': .5}
    #arrow_pos: 'bottom_mid'
    #background_color: (1, 0, 0, 1.0) #50% translucent red
    #border: [0, 0, 0, 0]    
''')

class CustomizeGaugeBubble(CenteredBubble):
    pass

NULL_LAP_TIME='--:--.---'

class Gauge(AnchorLayout):
    rcid = None
    settings = ObjectProperty(None)    
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    title = StringProperty('')
    data_bus = ObjectProperty(None)
    title_color   = ObjectProperty(DEFAULT_NORMAL_COLOR)
    normal_color  = ObjectProperty(DEFAULT_NORMAL_COLOR)
    
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)
        self.rcid = kwargs.get('rcid', self.rcid)
        self.data_bus = kwargs.get('dataBus', self.data_bus)
        self.settings = kwargs.get('settings', self.settings)

    @property
    def titleView(self):
        return self.ids.title

    def on_title(self, instance, value):
        try:
            if value is not None:
                view =  self.ids.title
                view.text = str(value)
        except: #the gauge may not have a title
            pass
                
    def on_title_color(self, instance, value):
        self.titleView.color = value
    
    def on_title_size(self, instance, value):
        view = self.titleView
        if view:
            view.font_size = value
    
    def update_title(self, channel_name, channel_meta):
        try:
            title = ''
            if channel_name is not None and channel_meta is not None:
                title = channel_meta.name
                if channel_meta.units and len(channel_meta.units):
                    title += '\n({})'.format(channel_meta.units)
            self.title = title
        except Exception as e:
            Logger.error('Gauge: Failed to update gauge title & units ' + str(e) + ' ' + str(title))
                 
    def on_channel_meta(self, channel_metas):
        pass
    
class SingleChannelGauge(Gauge):
    _valueView = None    
    channel = StringProperty(None, allownone=True)    
    value = NumericProperty(None, allownone=True)
    sensor_format = "{:.0f}"
    value_formatter = None
    precision = NumericProperty(DEFAULT_PRECISION)
    type = NumericProperty(DEFAULT_TYPE)
    halign = StringProperty(None)
    valign = StringProperty(None)

    def __init__(self, **kwargs):
        super(SingleChannelGauge, self).__init__(**kwargs)
        self.channel = kwargs.get('targetchannel', self.channel)
        self.value_formatter = self.sensor_formatter        

    @property
    def valueView(self):
        if not self._valueView:
            self._valueView = self.ids.value
        return self._valueView

    def on_halign(self, instance, value):
        self.valueView.halign = value 

    def on_valign(self, instance, value):
        self.valueView.valign = value 

    def on_channel_meta(self, channel_metas):
        channel = self.channel
        channel_meta = channel_metas.get(channel)
        if channel_meta is not None:
            self._update_display(channel_meta)            
            self.update_title(channel, channel_meta)
                
    def _update_gauge_meta(self):
        try:
            if self.settings:
                channel_meta = self.settings.runtimeChannels.channels.get(self.channel)
                self._update_display(channel_meta)
                self.update_title(self.channel, channel_meta)                
                self._update_channel_binding()
                self._update_channel_ranges()
        except Exception as e:
            Logger.error('Gauge: Error setting channel {}: {}'.format(self.channel, str(e)))
        
    def on_settings(self, instance, value):
        #Do I have an id so I can track my settings?
        if self.rcid:
            channel = self.settings.userPrefs.get_gauge_config(self.rcid)
            if channel:
                self.channel = channel
                self._update_gauge_meta()
                
    def on_data_bus(self, instance, value):
        self._update_channel_binding()
    
    def update_colors(self):
        view = self.valueView
        if view:
            view.color = self.normal_color

    def refresh_value(self, value):
        view = self.valueView
        if view:
            view.text = self.value_formatter(value)
            self.update_colors()
        
    def on_value(self, instance, value):
        self.refresh_value(value)

    def sensor_formatter(self, value):
        return "" if value is None else self.sensor_format.format(value)

    def update_value_format(self):
        if self.type == CHANNEL_TYPE_TIME:
            self.value_formatter = format_laptime
        else:
            self.sensor_format = '{:.' + str(self.precision) + 'f}'
            self.value_formatter = self.sensor_formatter
            
        self.refresh_value(self.value)

    def on_value_size(self, instance, value):
        view = self.valueView
        if view:
            view.font_size = value
    
    def on_channel(self, instance, value):
        self._update_gauge_meta()
        
    def _update_display(self, channel_meta):
        try:
            if channel_meta:
                self.min = channel_meta.min
                self.max = channel_meta.max
                self.precision = channel_meta.precision
                self.type = channel_meta.type if channel_meta.type is not CHANNEL_TYPE_UNKNOWN else self.type
            else:
                self.min = DEFAULT_MIN
                self.max = DEFAULT_MAX
                self.precision = DEFAULT_PRECISION
                self.value = DEFAULT_VALUE
                self.type = DEFAULT_TYPE
            self.update_value_format()
        except Exception as e:
            Logger.error('Gauge: Failed to update gauge min/max ' + str(e))
        
    def _update_channel_binding(self):
        dataBus = self.data_bus
        channel = self.channel
        if dataBus and channel:
            dataBus.addChannelListener(str(channel), self.setValue)
            dataBus.addMetaListener(self.on_channel_meta)
            
    def setValue(self, value):
        self.value = value
    
class CustomizableGauge(ButtonBehavior, SingleChannelGauge):
    _popup = None
    _customizeGaugeBubble = None
    warning = ObjectProperty(Range())
    alert = ObjectProperty(Range())
    min = NumericProperty(DEFAULT_MIN)
    max = NumericProperty(DEFAULT_MAX)
    _dismiss_customization_popup_trigger = None
    is_removable = BooleanProperty(True)
    is_channel_selectable = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(CustomizableGauge, self).__init__(**kwargs)
        self._dismiss_customization_popup_trigger = Clock.create_trigger(self._dismiss_popup, POPUP_DISMISS_TIMEOUT_LONG)

    def _remove_customization_bubble(self, *args):
        try:
            if self._customizeGaugeBubble: 
                self._customizeGaugeBubble.dismiss()
                self._customizeGaugeBubble = None
        except:
            pass

    def _get_warn_prefs_key(self, channel):
        return '{}.warn'.format(self.channel)        
    
    def _get_alert_prefs_key(self, channel):
        return '{}.alert'.format(self.channel)
            
    def _update_channel_ranges(self):
        channel = self.channel
        user_prefs = self.settings.userPrefs
        self.warning = user_prefs.get_range_alert(self._get_warn_prefs_key(channel), self.warning)
        self.alert   = user_prefs.get_range_alert(self._get_alert_prefs_key(channel), self.alert)

    def removeChannel(self):
        self._remove_customization_bubble()        
        channel = self.channel
        if channel:
            self.data_bus.removeChannelListener(channel, self.setValue)
        self.channel = None        

    def customizeGauge(self, *args):
        self._remove_customization_bubble()
        self.showChannelConfigDialog()

    def selectChannel(self, *args):
        self._remove_customization_bubble()
        self.showChannelSelectDialog()        

    def select_alert_color(self):
        value = self.value
        color = self.normal_color
        if self.alert and self.alert.is_in_range(value):
            color = self.alert.color
        elif self.warning and self.warning.is_in_range(value):
            color = self.warning.color
        return color
        
    def update_colors(self):
        view = self.valueView
        if view:
            view.color = self.select_alert_color()

    def showChannelSelectDialog(self):
        content = ChannelSelectView(settings=self.settings, channel=self.channel)
        content.bind(on_channel_selected=self.channel_selected)
        content.bind(on_channel_cancel=self._dismiss_popup)

        popup = Popup(title="Select Channel", content=content, size_hint=(0.5, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        self._dismiss_customization_popup_trigger()

    def on_channel_customization_close(self, instance, warn_range, alert_range, *args):
        try:
            self.warning = warn_range
            self.alert = alert_range
        except Exception as e:
            Logger.error("Gauge: Error customizing channel: " + str(e))
        self._dismiss_popup()
             
    def showChannelConfigDialog(self):          
        content = ChannelCustomizationView(settings=self.settings, channel=self.channel)
        content.bind(on_channel_customization_close=self.on_channel_customization_close)

        popup = Popup(title='Customize {}'.format(self.channel), content=content, size_hint=(0.6, 0.8))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        self._dismiss_customization_popup_trigger()

    def channel_selected(self, instance, value):
        if self.channel:
            self.data_bus.removeChannelListener(self.channel, self.setValue)
        self.value = None        
        self.channel = value
        self.settings.userPrefs.set_gauge_config(self.rcid, value)
        self._dismiss_popup()

    def popup_dismissed(self, *args):
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None

    def on_release(self):
        if not self.channel:
            self.showChannelSelectDialog()
        else:
            bubble = CustomizeGaugeBubble()
            buttons = []
            if self.is_removable: buttons.append(BubbleButton(text='Remove', on_press=lambda a:self.removeChannel()))
            if self.is_channel_selectable: buttons.append(BubbleButton(text='Select Channel', on_press=lambda a:self.selectChannel()))
            buttons.append(BubbleButton(text='Customize', on_press=lambda a:self.customizeGauge()))
            if len(buttons) == 1:
                buttons[0].dispatch('on_press')
            else:
                for b in buttons:
                    bubble.add_widget(b)
                    
                bubble_height = dp(150)
                bubble_width = dp(200)
                bubble.size =  (bubble_width, bubble_height)
                bubble.center_on_limited(self)
                bubble.auto_dismiss_timeout(POPUP_DISMISS_TIMEOUT_SHORT)
                self._customizeGaugeBubble = bubble
                self.add_widget(bubble)
    
