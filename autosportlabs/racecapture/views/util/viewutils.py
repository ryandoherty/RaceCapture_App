import kivy
kivy.require('1.9.1')
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.app import Builder
from kivy.properties import StringProperty

__all__ = ('format_laptime')

NULL_LAP_TIME = '--:--.---'
MIN_LAP_TIME=0

def format_laptime(time):
    if time == None:
        return NULL_LAP_TIME

    int_minute_value = int(time)
    fraction_minute_value = 60.0 * (time - float(int_minute_value))
    if time == MIN_LAP_TIME:
        return NULL_LAP_TIME
    else:
        return '{}:{}'.format(int_minute_value,'{0:06.3f}'.format(fraction_minute_value))
    
