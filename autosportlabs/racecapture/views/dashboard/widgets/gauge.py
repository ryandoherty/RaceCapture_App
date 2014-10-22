import kivy
kivy.require('1.8.0')
from kivy.properties import ListProperty, StringProperty, NumericProperty, ObjectProperty, DictProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from utils import kvFind, kvquery, dist
from installfix_garden_modernmenu import ModernMenu
from functools import partial
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

class Gauge(ButtonBehavior, AnchorLayout):
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
    
    
    #Popup menu
    menuTimeout = NumericProperty(0.1)
    menuClass = ObjectProperty(ModernMenu)
    cancelDistance = NumericProperty(10)
    menuArgs = DictProperty({})
    
    _popup = None
    
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)
        
        self.dataBus = kwargs.get('dataBus')
        self.channel = kwargs.get('channel')
        self.settings = kwargs.get('settings')
        self.menuArgs =  dict(
                creation_direction=-1,
                radius=dp(30),
                creation_timeout=0.2,
                dismiss_timeout=0.1,
                choices=[
                dict(text='Remove', index=1, callback=self.removeGauge),
                dict(text='Select Channel', index=2, callback=self.selectChannel),
                dict(text='Customize', index=3, callback=self.customizeGauge),
                ],
                item_args=dict(radius=dp(MENU_ITEM_RADIUS))
                )
        
    def removeGauge(self, *args):
        args[0].parent.dismiss()
        #this is a hack to prevent the modernmenu from grabbing the channel title widget when the title is blanked out
        #there's a bug in kvFind that needs to be fixed        
        Clock.schedule_once(lambda dt: self.removeChannel(), 0.2)

    def removeChannel(self):
        channel = self.channel
        if channel:
            self.dataBus.removeChannelListener(channel, self.setValue)
        self.channel = None        

    def customizeGauge(self, *args):
        args[0].parent.dismiss()
        self.showChannelConfigDialog()

    def selectChannel(self, *args):
        args[0].parent.dismiss()
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

    def on_touch_down(self, touch, *args):
        if self.collide_point(*touch.pos):
            t = partial(self.display_menu, touch)
            touch.ud['menu_timeout'] = t
            Clock.schedule_once(t, self.menuTimeout)
            return super(Gauge, self).on_touch_down(touch, *args)

    def on_touch_move(self, touch, *args):
        menuTimeout = touch.ud.get('menu_timeout')
        if self.collide_point(*touch.pos):
            if menuTimeout and dist(touch.pos, touch.opos) > self.cancelDistance:
                Clock.unschedule(menuTimeout)
            return super(Gauge, self).on_touch_move(touch, *args)

    def on_touch_up(self, touch, *args):
        if self.collide_point(*touch.pos):
            menuTimeout = touch.ud.get('menu_timeout')
            if menuTimeout:
                Clock.unschedule(menuTimeout)
            return super(Gauge, self).on_touch_up(touch, *args)

    def display_menu(self, touch, dt):
        if self.channel:
            parent = self.get_parent_window()
            center = touch.pos

            halfWidth = parent.width / 2
            halfHeight = parent.height / 2
            x = center[0] - halfWidth
            y = center[1] - halfHeight
            paddedRadius = MENU_ITEM_RADIUS * 1.4
            
            if x - paddedRadius < -halfWidth: x = -halfWidth + paddedRadius
            if x + paddedRadius > halfWidth: x = halfWidth - paddedRadius
            
            if y - paddedRadius < -halfHeight: y = -halfHeight + paddedRadius
            if y + paddedRadius > halfHeight: y= halfHeight -paddedRadius
            
            menu = self.menuClass(pos=(x, y), **self.menuArgs)
            
            self.get_parent_window().add_widget(menu)
            menu.start_display(touch)
            
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
                