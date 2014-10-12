import kivy
kivy.require('1.8.0')
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from utils import kvFind

DEFAULT_NORMAL_COLOR  = [1.0, 1.0 , 1.0, 1.0]
DEFAULT_WARNING_COLOR = [1.0, 0.79, 0.2 ,1.0]
DEFAULT_ALERT_COLOR   = [1.0, 0   , 0   ,1.0]

class Gauge(object):
    _valueView = None
    _titleView = None    
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    channel = StringProperty(None)    
    title = StringProperty('')
    value = NumericProperty(None)
    warning = NumericProperty(None)
    alert = NumericProperty(None)
    max = NumericProperty(None)
    title_color   = ObjectProperty(DEFAULT_NORMAL_COLOR)
    normal_color  = ObjectProperty(DEFAULT_NORMAL_COLOR)
    warning_color = ObjectProperty(DEFAULT_WARNING_COLOR)
    alert_color   = ObjectProperty(DEFAULT_ALERT_COLOR)
    
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)

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
            view.text = str(value)
            self.updateColors()

    def on_title(self, instance, value):
        if not value == None:
            view = self.titleView
            view.text = str(value)
            
    def on_title_color(self, instance, value):
        self.titleView.color = value

    def setValue(self, value):
        self.value = value
