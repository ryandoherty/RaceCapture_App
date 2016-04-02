import kivy
kivy.require('1.9.1')

from kivy.uix.spinner import Spinner

class MappedSpinner(Spinner):
    def __init__(self, **kwargs):
        self.valueMappings = {}
        self.keyMappings = {}
        self.values = []
        self.defaultValue = ''
        super(MappedSpinner, self).__init__(**kwargs)
        
    def setValueMap(self, valueMap, defaultValue):
        keyMappings = {}
        values = []
        sortedValues = sorted(valueMap)

        for item in sortedValues:
            values.append(valueMap[item])
            keyMappings[valueMap[item]] = item
            
        self.defaultValue = defaultValue
        self.valueMappings = valueMap
        self.keyMappings = keyMappings
        self.values = values
                    
    def setFromValue(self, value):
        self.text = str(self.valueMappings.get(value, self.defaultValue))

    def getValueFromKey(self, key):
        return self.keyMappings.get(key, None)
    
    def getSelectedValue(self):
        return self.getValueFromKey(self.text)

