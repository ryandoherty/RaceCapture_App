import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel
from kivy.properties import BoundedNumericProperty, ObjectProperty, BooleanProperty
Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/timedelta.kv')

MIN_TIME_DELTA = -99.0
MAX_TIME_DELTA = 99.0
OUT_OF_RANGE_VALUE = '--.-'

DEFAULT_AHEAD_COLOR  = [1.0, 0.0 , 1.0, 1.0]
DEFAULT_BEHIND_COLOR = [1.0, 0.65, 0.0 ,1.0]

class TimeDelta(FieldLabel):
    ahead_color = ObjectProperty(DEFAULT_AHEAD_COLOR)
    behind_color = ObjectProperty(DEFAULT_BEHIND_COLOR)
    value = BoundedNumericProperty(0, min=MIN_TIME_DELTA, max=MAX_TIME_DELTA, errorhandler=lambda x: MAX_TIME_DELTA if x > MAX_TIME_DELTA else MIN_TIME_DELTA)
    
    def __init__(self, **kwargs):
        super(TimeDelta, self).__init__(**kwargs)

    def is_ahead(self):
        return self.value <= 0
    
    def _updateView(self):
        self.color = self.ahead_color if self.is_ahead() else self.behind_color
         
    def on_reference_value(self, value):
        self.updateView()
        
    def on_value(self, instance, value):
        self.text = '{0:+1.1f}'.format(float(value))
        self._updateView()
