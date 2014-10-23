import kivy
kivy.require('1.8.0')
from kivy.properties import ListProperty, StringProperty, NumericProperty, ObjectProperty, DictProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.bubble import Bubble,BubbleButton
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from utils import kvFind, kvquery, dist
from functools import partial
from kivy.app import Builder
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectView
from autosportlabs.racecapture.views.channels.channelcustomizationview import ChannelCustomizationView
DEFAULT_NORMAL_COLOR  = [1.0, 1.0 , 1.0, 1.0]
DEFAULT_WARNING_COLOR = [1.0, 0.79, 0.2 ,1.0]
DEFAULT_ALERT_COLOR   = [1.0, 0   , 0   ,1.0]

DEFAULT_VALUE = None
DEFAULT_MIN = 0
DEFAULT_MAX = 100
DEFAULT_PRECISION = 0

MENU_ITEM_RADIUS = 100

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
    settings = ObjectProperty(None)    
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    channel = StringProperty(None, allownone=True)    
    title = StringProperty('')
    value = NumericProperty(None, allownone=True)
    valueFormat = "{:.0f}"
    precision = NumericProperty(DEFAULT_PRECISION)
    warning = NumericProperty(None)
    alert = NumericProperty(None)
    min = NumericProperty(DEFAULT_MIN)
    max = NumericProperty(DEFAULT_MAX)
    title_color   = ObjectProperty(DEFAULT_NORMAL_COLOR)
    normal_color  = ObjectProperty(DEFAULT_NORMAL_COLOR)
    warning_color = ObjectProperty(DEFAULT_WARNING_COLOR)
    alert_color   = ObjectProperty(DEFAULT_ALERT_COLOR)    
    pressed = ListProperty([0,0])
    dataBus = ObjectProperty(None)
    
    _popup = None
    
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)
        
        self.dataBus = kwargs.get('dataBus')
        self.channel = kwargs.get('channel')
        self.settings = kwargs.get('settings')
        
    def removeChannel(self):
        self.remove_widget(self._customizeGaugeBubble)        
        channel = self.channel
        if channel:
            self.dataBus.removeChannelListener(channel, self.setValue)
        self.channel = None        

    def customizeGauge(self, *args):
        self.remove_widget(self._customizeGaugeBubble)
        self.showChannelConfigDialog()

    def selectChannel(self, *args):
        self.remove_widget(self._customizeGaugeBubble)
        self.showChannelSelectDialog()        

    @property
    def valueView(self):
        if not self._valueView:
            self._valueView = kvFind(self, 'rcid', 'value')
        return self._valueView

    @property
    def titleView(self):
        return kvFind(self, 'rcid', 'title')

    def updateColors(self):
        value = self.value
        view = self.valueView
        if self.alert and self.alert.isInRange(value):
            view.color = self.alert_color
        elif self.warning and self.warning.isInRange(value):
            view.color = self.warning_color
        else:
            view.color = self.normal_color
        
    def on_value(self, instance, value):
        view = self.valueView
        if value != None:
            if view:
                view.text = self.valueFormat.format(value)
                self.updateColors()
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
        content = ChannelSelectView(settings=self.settings)
        content.bind(on_channel_selected=self.channelSelected)
        content.bind(on_channel_cancel=self.dismiss_popup)

        popup = Popup(title="Select Channel", content=content, size_hint=(0.5, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        
    def showChannelConfigDialog(self):          
        content = ChannelCustomizationView(settings=self.settings)
        content.bind(on_channel_customization_close=self.dismiss_popup)

        popup = Popup(title="Customize Channel", content=content, size_hint=(0.5, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        
    def channelSelected(self, instance, value):
        if self.channel:
            self.dataBus.removeChannelListener(self.channel, self.setValue)
        self.value = None        
        self.channel = value
        self.dismiss_popup()

    def popup_dismissed(self, *args):
        self._popup = None
        
    def dismiss_popup(self, *args):
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
            bubble = CustomizeGaugeBubble()
            bubble.add_widget(BubbleButton(text='Remove', on_press=lambda a:self.removeChannel()))
            bubble.add_widget(BubbleButton(text='Select Channel', on_press=lambda a:self.selectChannel()))
            bubble.add_widget(BubbleButton(text='Customize', on_press=lambda a:self.customizeGauge()))
            bubble.size =  (dp(200), dp(150))            
            self.add_widget(bubble)
            self._customizeGaugeBubble = bubble
            
            
            
                