import kivy
kivy.require('1.9.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel
from kivy.properties import BoundedNumericProperty, StringProperty, NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge, SingleChannelGauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/laptime.kv')

MIN_LAP_TIME=0
MAX_LAP_TIME=99.999
    
class Laptime(SingleChannelGauge):
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
                    view.text = self.NULL_LAP_TIME
                else:
                    view.text = '{}:{}'.format(intMinuteValue,'{0:06.3f}'.format(fractionMinuteValue))
        self.updateColors()

    def on_halign(self, instance, value):
        self.valueView.halign = value 
        
    def on_touch_down(self, touch, *args):
        pass

    def on_touch_move(self, touch, *args):
        pass

    def on_touch_up(self, touch, *args):
        pass
        

class CurrentLaptime(Laptime):
    NULL_LAP_TIME='--:--.---'
    last_laptime = NumericProperty(None)
    elapsed_time = NumericProperty(None)
    predicted_time = NumericProperty(None)
    current_lap = NumericProperty(None)
    
    def on_data_bus(self, instance, value):
        print("currentLaptime onDAtabus")
        dataBus = self.data_bus
        channel = self.channel
        if dataBus and channel:
            dataBus.addMetaListener(self.on_channel_meta)
            dataBus.addChannelListener("LapTime", self.set_lap_time)
            dataBus.addChannelListener("ElapsedTime" , self.set_elapsed_time)
            dataBus.addChannelListener("PredTime", self.set_predicted_time)
            dataBus.addChannelListener("LapCount", self.set_lap_count)
            dataBus.addChannelListener("CurrentLap", self.set_current_lap)

    def set_lap_time(self, value):
        pass
    
    def set_elapsed_time(self, value):
        pass
    
    def set_predicted_time(self, value):
        pass
    
    def set_lap_count(self, value):
        pass
    
    def set_current_lap(self, value):
        pass
        