import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel
from kivy.properties import BoundedNumericProperty, StringProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/laptime.kv')

MIN_LAP_TIME=0
MAX_LAP_TIME=99.999

class Laptime(Gauge):
    NULL_LAP_TIME='--:--.---'
    value = BoundedNumericProperty(0, min=MIN_LAP_TIME, max=MAX_LAP_TIME, errorhandler=lambda x: MAX_LAP_TIME if x > MAX_LAP_TIME else MIN_LAP_TIME)
    halign = StringProperty(None)
        
    def __init__(self, **kwargs):
        super(Laptime, self).__init__(**kwargs)

    def on_value(self, instance, value):
        view = self.valueView
        if view:
            if value == None:
                view.text = self.NULL_LAP_TIME
            else:
                intMinuteValue = int(value)
                fractionMinuteValue = 60.0 * (value - float(intMinuteValue))
                if value == MIN_LAP_TIME:
                    view.text = NULL_LAP_TIME
                else:
                    view.text = '{}:{}'.format(intMinuteValue,'{0:2.3f}'.format(fractionMinuteValue))
        self.updateColors()

    def on_halign(self, instance, value):
        self.valueView.halign = value 
        
    def on_touch_down(self, touch, *args):
        pass

    def on_touch_move(self, touch, *args):
        pass

    def on_touch_up(self, touch, *args):
        pass
        
        