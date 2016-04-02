import kivy
kivy.require('1.9.1')
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.app import Builder

Builder.load_file('autosportlabs/widgets/separator.kv')

class HLineSeparator(Label):
    pass

class HSeparator(Label):
    pass
    
class VSeparator(Widget):
    pass
    
class HSeparatorMinor(Label):
    def __init__(self, **kwargs):
        super(HSeparatorMinor, self).__init__(**kwargs)
