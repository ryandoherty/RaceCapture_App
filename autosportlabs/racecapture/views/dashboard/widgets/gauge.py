import kivy
kivy.require('1.8.0')
from kivy.properties import ListProperty, StringProperty, NumericProperty, ObjectProperty, DictProperty
from kivy.clock import Clock
from utils import kvFind, dist
from kivy.uix.anchorlayout import AnchorLayout
from installfix_garden_modernmenu import ModernMenu
from functools import partial

DEFAULT_NORMAL_COLOR  = [1.0, 1.0 , 1.0, 1.0]
DEFAULT_WARNING_COLOR = [1.0, 0.79, 0.2 ,1.0]
DEFAULT_ALERT_COLOR   = [1.0, 0   , 0   ,1.0]

class Gauge(AnchorLayout):
    _valueView = None
    _titleView = None    
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    channel = StringProperty(None)    
    title = StringProperty('')
    value = NumericProperty(None)
    valueFormat = "{:.0f}"
    precision = NumericProperty(0)
    warning = NumericProperty(None)
    alert = NumericProperty(None)
    max = NumericProperty(None)
    title_color   = ObjectProperty(DEFAULT_NORMAL_COLOR)
    normal_color  = ObjectProperty(DEFAULT_NORMAL_COLOR)
    warning_color = ObjectProperty(DEFAULT_WARNING_COLOR)
    alert_color   = ObjectProperty(DEFAULT_ALERT_COLOR)    
    pressed = ListProperty([0,0])
    
    timeout = NumericProperty(0.1)
    menu_cls = ObjectProperty(ModernMenu)
    cancel_distance = NumericProperty(10)
    menu_args = DictProperty({})
    
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)
        
        self.menu_args =  dict(
                creation_direction=-1,
                radius=30,
                creation_timeout=.2,
                choices=[
                dict(text='Remove', index=1, callback=self.removeGauge),
                dict(text='Select Channel', index=2, callback=self.selectChannel),
                dict(text='Customize', index=3, callback=self.customizeGauge),
                ])
        
    def removeGauge(self, *args):
        print "remove Gauge"
        args[0].parent.dismiss()        

    def customizeGauge(self, *args):
        print "customize gauge"
        args[0].parent.dismiss()

    def selectChannel(self, *args):
        print "select channel"
        args[0].parent.dismiss()

    @property
    def valueView(self):
        if not self._valueView:
            self._valueView = kvFind(self, 'rcid', 'value')
        return self._valueView

    @property
    def titleView(self):
        if not self._titleView:
            self._titleView = kvFind(self, 'rcid', 'title')
        return self._titleView

    def updateColors(self):
        value = self.value
        view = self.valueView
        if self.alert and value >= self.alert:
            view.color = self.alert_color
        elif self.warning and value >=self.warning:
            view.color = self.warning_color
        else:
            view.color = self.normal_color
        
    def on_value(self, instance, value):
        if not value == None:
            view = self.valueView
            if view:
                view.text = self.valueFormat.format(value)
                self.updateColors()

    def on_title(self, instance, value):
        if not value == None:
            view = self.titleView
            if view:
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
            Clock.schedule_once(t, self.timeout)
            return super(Gauge, self).on_touch_down(touch, *args)

    def on_touch_move(self, touch, *args):
        if self.collide_point(*touch.pos):
            if (
                touch.ud['menu_timeout'] and
                dist(touch.pos, touch.opos) > self.cancel_distance
            ):
                Clock.unschedule(touch.ud['menu_timeout'])
            return super(Gauge, self).on_touch_move(touch, *args)

    def on_touch_up(self, touch, *args):
        if self.collide_point(*touch.pos):
            if touch.ud.get('menu_timeout'):
                Clock.unschedule(touch.ud['menu_timeout'])
            return super(Gauge, self).on_touch_up(touch, *args)

    def display_menu(self, touch, dt):
        if self.channel:
            menu = self.menu_cls(center=touch.pos, **self.menu_args)
            self.add_widget(menu)
            menu.start_display(touch)
        else:
            self.showChannelSelectDialog()
            
    def showChannelSelectDialog(self):
        pass
        
        
        
            
