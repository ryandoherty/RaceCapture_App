import kivy
kivy.require('1.9.1')

from kivy.uix.textinput import TextInput


class BetterTextInput(TextInput):

    max_chars = 200000

    def insert_text(self, substring, from_undo=False):
        if not from_undo and (len(self.text)+len(substring) > self.max_chars):
            return
        super(BetterTextInput, self).insert_text(substring, from_undo)
