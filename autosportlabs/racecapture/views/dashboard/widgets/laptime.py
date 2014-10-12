import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel
from kivy.properties import BoundedNumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/laptime.kv')

MIN_LAP_TIME=0
MAX_LAP_TIME=99.999
NULL_LAP_TIME='--:--.---'

class Laptime(FieldLabel, Gauge):
#    value = BoundedNumericProperty(None, min=MIN_LAP_TIME, max=MAX_LAP_TIME, errorhandler=lambda x: MAX_LAP_TIME if x > MAX_LAP_TIME else MIN_LAP_TIME)    
    def __init__(self, **kwargs):
        super(Laptime, self).__init__(**kwargs)
        self.text = NULL_LAP_TIME

    def on_value(self, instance, value):
        print('onvalue' + str(value))
        intMinuteValue = int(value)
        fractionMinuteValue = 60.0 * (value - float(intMinuteValue))
        if value == MIN_LAP_TIME:
            self.text = NULL_LAP_TIME
        else:
            self.text = '{}:{}'.format(intMinuteValue,'{0:2.3f}'.format(fractionMinuteValue))
