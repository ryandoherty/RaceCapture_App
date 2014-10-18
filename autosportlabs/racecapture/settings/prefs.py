from kivy.event import EventDispatcher
from kivy.properties import OptionProperty, NumericProperty, AliasProperty,\
    DictProperty
from kivy.clock import Clock

UNITS_KM    = 'km'
UNITS_MILES = 'miles'

class Range(EventDispatcher):
    high = NumericProperty(0)
    low = NumericProperty(0)
    
class UserPrefs(EventDispatcher):
    _scheduleSave = None
    _rangeAlerts = {}
    speedUnits = OptionProperty("None", options=[UNITS_KM, UNITS_MILES], default=UNITS_MILES)
    alerts = DictProperty({})
    
    blah = NumericProperty(3)
    
    def __init__(self, **kwargs):
        self._scheduleSave = Clock.create_trigger(self.savePrefs, 3)

    def on_alerts(self, value):
        print(str(value))
        
    def _get_rangeAlert(self):
        return 'foo'
    
    def _set_rangeAlert(self, value):
        print(str(value[0]))
        #self._rangeAlerts[key] = value
        pass

    rangeAlerts = AliasProperty(_get_rangeAlert, _set_rangeAlert)
        
    def on_speedUnits(self, instance, value):
        self._scheduleSave()
            
    def on_rangeAlerts(self, instance, value):
        self._scheduleSave()
                
    def savePrefs(self, *largs):
        print('saving prefs')
    
    
        
        
        
    