from kivy.properties import OptionProperty, NumericProperty

UNITS_KM    = 'km'
UNITS_MILES = 'miles'

class UserPrefs(object):
    speedUnits = OptionProperty("None", options=[UNITS_KM, UNITS_MILES], default=UNITS_MILES)    
    prefs = {}
    
    def setPref(self, key, value):
        self.prefs[key] = value
        
    def getPref(self, key):
        return self.prefs.get(key)
    
    def __init__(self, **kwargs):
        pass
    
        
        
        
    