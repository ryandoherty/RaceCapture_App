import kivy
kivy.require('1.9.1')

from kivy.uix.spinner import Spinner
from kivy import Logger

class MappedSpinner(Spinner):
    def __init__(self, **kwargs):
        self.valueMappings = {}
        self.keyMappings = {}
        self.values = []
        self.defaultValue = ''
        super(MappedSpinner, self).__init__(**kwargs)
        
    def setValueMap(self, valueMap, defaultValue, sort_key=None):
        """
        Sets the displayed and actual values for the spinner
        :param valueMap: Dict of value: Display Value items to display
        :param defaultValue: Default value
        :param sort_key: Optional function that will return the actual value to sort on. See
                        https://docs.python.org/2/howto/sorting.html#key-functions
        :return: None
        """
        keyMappings = {}
        values = []
        sortedValues = sorted(valueMap, key=sort_key)

        for item in sortedValues:
            values.append(valueMap[item])
            keyMappings[valueMap[item]] = item

        self.defaultValue = defaultValue
        self.valueMappings = valueMap
        self.keyMappings = keyMappings
        self.values = values
        self.text = defaultValue

    def setFromValue(self, value):
        self.text = str(self.valueMappings.get(value, self.defaultValue))

    def getValueFromKey(self, key):
        return self.keyMappings.get(key, None)
    
    def getSelectedValue(self):
        return self.getValueFromKey(self.text)

