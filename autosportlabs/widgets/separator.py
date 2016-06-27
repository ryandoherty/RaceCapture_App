import kivy
kivy.require('1.9.1')
from kivy.uix.widget import Widget
from kivy.app import Builder
from autosportlabs.uix.baselabel import BaseLabel

Builder.load_file('autosportlabs/widgets/separator.kv')

class HLineSeparator(BaseLabel):
    pass

class HSeparator(BaseLabel):
    pass
    
class VSeparator(Widget):
    pass
    
class HSeparatorMinor(BaseLabel):
    def __init__(self, **kwargs):
        super(HSeparatorMinor, self).__init__(**kwargs)
