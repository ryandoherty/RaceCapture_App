import kivy
kivy.require('1.9.1')
from kivy.uix.label import Label
from kivy.uix.button import ButtonBehavior
from fieldlabel import FieldLabel

class LabelButton(ButtonBehavior, FieldLabel):
    pass