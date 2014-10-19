from kivy.event import EventDispatcher
from kivy.properties import OptionProperty, NumericProperty
from kivy.clock import Clock


class Range(EventDispatcher):
    high = NumericProperty(0)
    low = NumericProperty(0)
    
    def __init__(self, **kwargs):
        self.low = kwargs.get('low', self.low)
        self.high = kwargs.get('high', self.high)
    
    def isInRange(self, value):
        return value >= self.low and value <= self.high
    
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
        
    def getrangeAlert(self, key):
        return _rangeAlerts.get(key)
        
                
    def savePrefs(self, *largs):
        print('saving prefs')
    
    
        
        
        
    