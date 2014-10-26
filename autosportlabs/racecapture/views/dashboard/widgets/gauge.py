import kivy
kivy.require('1.8.0')
from kivy.properties import ListProperty, StringProperty, NumericProperty, ObjectProperty, DictProperty,\
    BooleanProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.bubble import Bubble,BubbleButton
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from utils import kvFind, kvquery, dist
from functools import partial
from kivy.app import Builder
from autosportlabs.racecapture.settings.prefs import Range
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from autosportlabs.racecapture.views.channels.channelcustomizationview import ChannelCustomizationView
DEFAULT_NORMAL_COLOR  = [1.0, 1.0 , 1.0, 1.0]

DEFAULT_VALUE = None
DEFAULT_MIN = 0
DEFAULT_MAX = 100
DEFAULT_PRECISION = 0

MENU_ITEM_RADIUS = 100
POPUP_DISMISS_TIMEOUT_SHORT = 2.0
POPUP_DISMISS_TIMEOUT_LONG = 60.0

Builder.load_string('''
<CustomizeGaugeBubble>
    orientation: 'vertical'
    size_hint: (None, None)
    pos_hint: {'center_x': .5, 'y': .5}
    #arrow_pos: 'bottom_mid'
    #background_color: (1, 0, 0, 1.0) #50% translucent red
    #border: [0, 0, 0, 0]    
''')

class CustomizeGaugeBubble(Bubble):
    pass

class Gauge(ButtonBehavior, AnchorLayout):
    _customizeGaugeBubble = None
    _valueView = None
    is_removable = BooleanProperty(True)
    is_channel_selectable = BooleanProperty(True)
    settings = ObjectProperty(None)    
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    channel = StringProperty(None, allownone=True)    
    title = StringProperty('')
    value = NumericProperty(None, allownone=True)
    valueFormat = "{:.0f}"
    precision = NumericProperty(DEFAULT_PRECISION)
    warning = ObjectProperty(Range())
    alert = ObjectProperty(Range())
    min = NumericProperty(DEFAULT_MIN)
    max = NumericProperty(DEFAULT_MAX)
    title_color   = ObjectProperty(DEFAULT_NORMAL_COLOR)
    normal_color  = ObjectProperty(DEFAULT_NORMAL_COLOR)
    pressed = ListProperty([0,0])
    dataBus = ObjectProperty(None)
    
    _popup = None

    _dismiss_customization_bubble_trigger = None
    _dismiss_customization_popup_trigger = None
    
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)
        
        self.dataBus = kwargs.get('dataBus')
        channel = kwargs.get('channel')
        settings = kwargs.get('settings')
        if settings:
            userPrefs = settings.userPrefs
            
            self.warning = userPrefs.getRangeAlert(self._get_warn_prefs_key(channel), self.warning)
            self.alert   = userPrefs.getRangeAlert(self._get_alert_prefs_key(channel), self.alert)        
                                                                 
            self.channel = channel
            self.settings = settings
            
        self._dismiss_customization_bubble_trigger = Clock.create_trigger(self._remove_customization_bubble, POPUP_DISMISS_TIMEOUT_SHORT)
        self._dismiss_customization_popup_trigger = Clock.create_trigger(self._dismiss_popup, POPUP_DISMISS_TIMEOUT_LONG)
            
        
    def _get_warn_prefs_key(self, channel):
        return '{}.warn'.format(self.channel)        
    
    def _get_alert_prefs_key(self, channel):
        return '{}.alert'.format(self.channel)
        
    def _remove_customization_bubble(self, *args):
        try:
            if self._customizeGaugeBubble:
                self.get_parent_window().remove_widget(self._customizeGaugeBubble)
                self._customizeGaugeBubble = None
        except:
            pass
            
    def removeChannel(self):
        self._remove_customization_bubble()        
        channel = self.channel
        if channel:
            self.dataBus.removeChannelListener(channel, self.setValue)
        self.channel = None        

    def customizeGauge(self, *args):
        self._remove_customization_bubble()
        self.showChannelConfigDialog()

    def selectChannel(self, *args):
        self._remove_customization_bubble()
        self.showChannelSelectDialog()        

    @property
    def valueView(self):
        if not self._valueView:
            self._valueView = kvFind(self, 'rcid', 'value')
        return self._valueView

    @property
    def titleView(self):
        return kvFind(self, 'rcid', 'title')

    def updateColors(self, view):
        value = self.value
        if self.alert and self.alert.isInRange(value):
            view.color = self.alert.color
        elif self.warning and self.warning.isInRange(value):
            view.color = self.warning.color
        else:
            view.color = self.normal_color
        
    def on_value(self, instance, value):
        view = self.valueView
        if value != None:
            if view:
                view.text = self.valueFormat.format(value)
                self.updateColors(view)
        else:
            view.text=''

    def on_title(self, instance, value):
        if not value == None:
            view =  kvFind(self, 'rcid', 'title')
            view.text = str(value)

    def on_precision(self, instance, value):
        self.valueFormat = '{:.' + str(value) + 'f}'
        
    def on_title_color(self, instance, value):
        self.titleView.color = value

    def on_value_size(self, instance, value):
        view = self.valueView
        if view:
            view.font_size = value
    
    def on_title_size(self, instance, value):
        view = self.titleView
        if view:
            view.font_size = value
            
    def setValue(self, value):
        self.value = value
            
    def showChannelSelectDialog(self):  
        content = ChannelSelectView(settings=self.settings, channel=self.channel)
        content.bind(on_channel_selected=self.channel_selected)
        content.bind(on_channel_cancel=self._dismiss_popup)

        popup = Popup(title="Select Channel", content=content, size_hint=(0.5, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        self._dismiss_customization_popup_trigger()
        
    
    def on_channel_customization_close(self, instance, *args):
        try:
            self.warning = args[0]
            self.alert = args[1]
        except Exception as e:
            print("Error customizing channel: " + str(e))
            
        self._dismiss_popup()
             
    def showChannelConfigDialog(self):          
        content = ChannelCustomizationView(settings=self.settings, channel=self.channel)
        content.bind(on_channel_customization_close=self.on_channel_customization_close)

        popup = Popup(title='Customize {}'.format(self.channel), content=content, size_hint=(0.6, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        self._dismiss_customization_popup_trigger()
        
    
    def channel_selected(self, instance, value):
        if self.channel:
            self.dataBus.removeChannelListener(self.channel, self.setValue)
        self.value = None        
        self.channel = value
        self._dismiss_popup()

    def popup_dismissed(self, *args):
        self._popup = None
        
    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None
                
    def on_channel(self, instance, value):
        try:
            self.updateDisplay()
            self.updateTitle()
            self.updateChannelBinding()
        except Exception as e:
            print('Error setting channel () ()'.format(value, str(e)))
        
    def on_dataBus(self, instance, value):
        self.updateChannelBinding()

    def updateTitle(self):
        try:
            channel = self.channel
            if channel:
                channelMeta = self.settings.systemChannels.channels.get(channel)
                title = channelMeta.name
                if channelMeta.units and len(channelMeta.units):
                    title += '\n({})'.format(channelMeta.units)
                self.title = title
            else:
                self.title = ''
        except Exception as e:
            print('Failed to update gauge title & units ' + str(e))
        
    def updateDisplay(self):
        try:
            channelMeta = self.settings.systemChannels.channels.get(self.channel)
            if channelMeta:
                self.min = channelMeta.min
                self.max = channelMeta.max
                self.precision = channelMeta.precision
            else:
                self.min = DEFAULT_MIN
                self.max = DEFAULT_MAX
                self.precision = DEFAULT_PRECISION
                self.value = DEFAULT_VALUE
        except Exception as e:
            print('Failed to update gauge min/max ' + str(e))
        
    def updateChannelBinding(self):
        dataBus = self.dataBus
        channel = self.channel
        if dataBus and channel:
            dataBus.addChannelListener(str(channel), self.setValue)
            
    def on_release(self):
        if not self.channel:
            self.showChannelSelectDialog()
        else:
            if not self._customizeGaugeBubble:
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
                    bubble.size =  (dp(200), dp(150))            
                    self.get_parent_window().add_widget(bubble)
                    self._customizeGaugeBubble = bubble
                    self._dismiss_customization_bubble_trigger()
            
            
                