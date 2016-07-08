import kivy
kivy.require('1.9.1')
from valuefield import ValueField
import re


class BetterTextInput(ValueField):
    """
    A better text input for forms. Allows for limiting # of characters and using a regex to also limit characters
    entered.
    """

    def __init__(self, max_chars=200000, regex=None, **kwargs):
        super(BetterTextInput, self).__init__(**kwargs)
        self.font_size = self.height * 0.20
        self.max_chars = max_chars
        self.regex = regex

    def insert_text(self, substring, from_undo=False):
        if not from_undo and (len(self.text)+len(substring) > self.max_chars):
            return

        if self.regex:
            pattern = re.compile(self.regex)
            substring = re.sub(pattern, '', substring)

        super(BetterTextInput, self).insert_text(substring, from_undo=from_undo)
