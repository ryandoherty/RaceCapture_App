from kivy.event import EventDispatcher
from kivy.properties import OptionProperty, NumericProperty,\
    ListProperty
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
import json


class Range(EventDispatcher):
    DEFAULT_WARN_COLOR = [1.0, 0.84, 0.0, 1.0]
    DEFAULT_ALERT_COLOR = [1.0, 0.0, 0.0, 1.0]
    max = NumericProperty(0)
    min = NumericProperty(0)
    color = ListProperty([1.0, 1.0, 1.0, 1.0])
    
    def __init__(self, **kwargs):
        self.min = kwargs.get('min', self.min)
        self.max = kwargs.get('max', self.max)
        self.color = kwargs.get('color', self.color)
        
    def isInRange(self, value):
        return value >= self.min and value <= self.max
    
class UserPrefs(EventDispatcher):
    UNITS_KM = 'km'
    UNITS_MILE = 'mile'
    _schedule_save = None
    _prefs_dict = {'range_alerts': {}}
    store = None
    prefs_file = None

    #properties    
    speed_units = OptionProperty('mile', options=[UNITS_KM, UNITS_MILE], default=UNITS_MILE)
    distance_units = OptionProperty('mile', options=[UNITS_KM, UNITS_MILE], default=UNITS_MILE)
    
    def __init__(self, **kwargs):
        self._schedule_save = Clock.create_trigger(self.save, 10)
        self.bind(speed_units=self._schedule_save)
        self.bind(distance_units=self._schedule_save)
        self.prefs_file = kwargs.get('data_dir')+'/prefs.json'
        self.load()

    def set_range_alert(self, key, range_alert):
        self._prefs_dict["range_alerts"][key] = range_alert
        self._schedule_save()
        
    def get_range_alert(self, key, default=None):
        return self._prefs_dict["range_alerts"].get(key)

    def save(self):
        print('saving prefs')
        json.dump(self._prefs_dict, open(self.prefs_file, mode='w+'))

    def load(self):
        print('loading prefs')
        try:
            self._prefs_dict = json.load(open(self.prefs_file))
        except:
            print "No prefs file found"

    
