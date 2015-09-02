from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.config import ConfigParser
import json
import os
from os import path
from os.path import dirname, expanduser, sep

class Range(EventDispatcher):
    DEFAULT_WARN_COLOR = [1.0, 0.84, 0.0, 1.0]
    DEFAULT_ALERT_COLOR = [1.0, 0.0, 0.0, 1.0]
    max = NumericProperty(None)
    min = NumericProperty(None)
    color = ListProperty([1.0, 1.0, 1.0, 1.0])
    
    def __init__(self, minimum=None, maximum=None, **kwargs):
        self.min = minimum
        self.max = maximum
        self.color = kwargs.get('color', self.color)

    def is_in_range(self, value):
        min = self.min
        max = self.max
        return (min and max) and self.min <= value <= self.max

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
    _schedule_save = None
    _prefs_dict = {'range_alerts': {}, 'gauge_settings':{}}
    store = None
    prefs_file_name = 'prefs.json'
    prefs_file = None
    config = None
    data_dir = '.'
    user_files_dir = '.'

    def __init__(self, data_dir, user_files_dir, save_timeout=2, **kwargs):
        self.data_dir = data_dir
        self.user_files_dir = user_files_dir
        self.prefs_file = path.join(self.data_dir, self.prefs_file_name)
        self.load()
        self._schedule_save = Clock.create_trigger(self.save, save_timeout)

    def set_range_alert(self, key, range_alert):
        self._prefs_dict["range_alerts"][key] = range_alert
        self._schedule_save()
        
    def get_range_alert(self, key, default=None):
        return self._prefs_dict["range_alerts"].get(key, default)

    def set_gauge_config(self, gauge_id, channel):
        self._prefs_dict["gauge_settings"][gauge_id] = channel
        self._schedule_save()

    def get_gauge_config(self, gauge_id):
        return self._prefs_dict["gauge_settings"].get(gauge_id, False)

    def save(self, *largs):
        with open(self.prefs_file, 'w+') as prefs_file:
            data = self.to_json()
            prefs_file.write(data)

    def set_config_defaults(self):
        self.config.adddefaultsection('preferences')
        self.config.setdefault('preferences', 'distance_units', 'miles')
        self.config.setdefault('preferences', 'temperature_units', 'Fahrenheit')
        self.config.setdefault('preferences', 'show_laptimes', 1)
        self.config.setdefault('preferences', 'startup_screen', 'Home Page')
        default_user_files_dir = self.user_files_dir
        self.config.setdefault('preferences', 'config_file_dir', default_user_files_dir )
        self.config.setdefault('preferences', 'firmware_dir', default_user_files_dir )
        self.config.setdefault('preferences', 'first_time_setup', True)
        self.config.setdefault('preferences', 'send_telemetry', False)
        self.config.setdefault('preferences', 'last_dash_screen', 'gaugeView')

    def load(self):
        print("the data dir " + self.data_dir)
        self.config = ConfigParser()
        self.config.read(os.path.join(self.data_dir, 'preferences.ini'))
        self.set_config_defaults()

        self._prefs_dict = {'range_alerts': {}, 'gauge_settings':{}}

        try:
            with open(self.prefs_file, 'r') as data:
                content = data.read()
                content_dict = json.loads(content)

                if content_dict.has_key("range_alerts"):
                    for name, settings in content_dict["range_alerts"].iteritems():
                        self._prefs_dict["range_alerts"][name] = Range.from_dict(settings)

                if content_dict.has_key("gauge_settings"):
                    for id, channel in content_dict["gauge_settings"].iteritems():
                        self._prefs_dict["gauge_settings"][id] = channel

        except Exception:
            pass
        
    def get_pref(self, section, option):
        return self.config.get(section, option)
    
    def set_pref(self, section, option, value):
        self.config.set(section, option, value)
        self.config.write()

    def to_json(self):
        data = {'range_alerts': {}, 'gauge_settings':{}}

        for name, range_alert in self._prefs_dict["range_alerts"].iteritems():
            data["range_alerts"][name] = range_alert.to_dict()

        for id, channel in self._prefs_dict["gauge_settings"].iteritems():
            data["gauge_settings"][id] = channel

        return json.dumps(data)
