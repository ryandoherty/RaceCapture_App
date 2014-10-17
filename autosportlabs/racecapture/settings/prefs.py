from kivy.properties import NumericProperty

UNITS_KM    = 1
UNITS_MILES = 2

class UserPrefs(object):
    speedUnits = NumericProperty(UNITS_KM)
    
    def __init__(self, **kwargs):
        pass
    
        
        
        
    