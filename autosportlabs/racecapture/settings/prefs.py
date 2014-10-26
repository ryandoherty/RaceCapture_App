from kivy.event import EventDispatcher
from kivy.properties import OptionProperty, NumericProperty,\
    ListProperty
from kivy.clock import Clock
import json


class Range(EventDispatcher):
    DEFAULT_WARN_COLOR = [1.0, 0.84, 0.0, 1.0]
    DEFAULT_ALERT_COLOR = [1.0, 0.0, 0.0, 1.0]
    max = NumericProperty(0)
    min = NumericProperty(0)
    color = ListProperty([1.0, 1.0, 1.0, 1.0])
    
    def __init__(self, minimum=0, maximum=0, **kwargs):
        self.min = minimum
        self.max = maximum
        self.color = kwargs.get('color', self.color)

    def is_in_range(self, value):
        return self.min <= value <= self.max

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {'min': self.min,
                'max': self.max,
                'color': self.color
                }

    @staticmethod
    def from_json(range_json):
        range_dict = json.loads(range_json)
        return Range.from_dict(range_dict)

    @staticmethod
    def from_dict(range_dict):
        return Range(minimum=range_dict['min'], maximum=range_dict['max'], color=range_dict['color'])
    
class UserPrefs(EventDispatcher):
    UNITS_KM = 'km'
    UNITS_MILE = 'mile'
    _schedule_save = None
    _prefs_dict = {'range_alerts': {}}
    store = None
    prefs_file_name = 'prefs.json'
    prefs_file = None

    #properties    
    speed_units = OptionProperty('mile', options=[UNITS_KM, UNITS_MILE], default=UNITS_MILE)
    distance_units = OptionProperty('mile', options=[UNITS_KM, UNITS_MILE], default=UNITS_MILE)
    
    def __init__(self, data_dir, save_timeout=10, **kwargs):
        self._schedule_save = Clock.create_trigger(self.save, save_timeout)
        self.bind(speed_units=self._schedule_save)
        self.bind(distance_units=self._schedule_save)
        self.prefs_file = data_dir+'/'+self.prefs_file_name
        self.load()

    def set_range_alert(self, key, range_alert):
        self._prefs_dict["range_alerts"][key] = range_alert
        self._schedule_save()
        
    def get_range_alert(self, key, default=None):
        return self._prefs_dict["range_alerts"].get(key, default)

    def save(self, *largs):
        with open(self.prefs_file, 'w+') as prefs_file:
            data = self.to_json()
            prefs_file.write(data)

    def load(self):
        self._prefs_dict = {'range_alerts': {}}
        try:
            with open(self.prefs_file, 'r') as data:
                content = data.read()
                content_dict = json.loads(content)

                for name, settings in content_dict["range_alerts"].iteritems():
                    self._prefs_dict["range_alerts"][name] = Range.from_dict(settings)

        except IOError:
            pass

    def to_json(self):
        data = {'range_alerts': {}}

        for name, range_alert in self._prefs_dict["range_alerts"].iteritems():
            data["range_alerts"][name] = range_alert.to_dict()

        return json.dumps(data)
