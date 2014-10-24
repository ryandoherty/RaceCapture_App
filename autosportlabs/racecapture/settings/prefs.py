from kivy.event import EventDispatcher
from kivy.properties import OptionProperty, NumericProperty,\
    ListProperty
from kivy.clock import Clock


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
    UNITS_KM    = 'km'
    UNITS_MILE = 'mile'
    _scheduleSave = None
    _rangeAlerts = {}

    #properties    
    speedUnits = OptionProperty('mile', options=[UNITS_KM, UNITS_MILE], default=UNITS_MILE)
    distanceUnits = OptionProperty('mile', options=[UNITS_KM, UNITS_MILE], default=UNITS_MILE)
    
    def __init__(self, **kwargs):
        self._scheduleSave = Clock.create_trigger(self.savePrefs, 10)
        self.bind(speedUnits=self._scheduleSave)
        self.bind(distanceUnits=self._scheduleSave)

    def setRangeAlert(self, key, rangeAlert):
        self._rangeAlerts[key] = rangeAlert
        self._scheduleSave();
        
    def getRangeAlert(self, key, default=None):
        return self._rangeAlerts.get(key, default)
        
                
    def savePrefs(self, *largs):
        print('saving prefs')
    
    
        
        
        
    