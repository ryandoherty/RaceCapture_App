import kivy
kivy.require('1.8.0')
from kivy.properties import StringProperty, NumericProperty, ObjectProperty

DEFAULT_NORMAL_COLOR  = [1.0, 1.0 , 1.0, 1.0]
DEFAULT_WARNING_COLOR = [1.0, 0.79, 0.2 ,1.0]
DEFAULT_ALERT_COLOR   = [1.0, 0   , 0   ,1.0]

class Gauge(object):
    title = StringProperty('')
    value = NumericProperty(None)
    warning = NumericProperty(None)
    alert = NumericProperty(None)
    max = NumericProperty(None)
    normal_color = ObjectProperty(DEFAULT_NORMAL_COLOR)
    warning_color = ObjectProperty(DEFAULT_WARNING_COLOR)
    alert_color = ObjectProperty(DEFAULT_ALERT_COLOR)
    
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)
