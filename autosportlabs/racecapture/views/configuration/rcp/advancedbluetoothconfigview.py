#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from utils import *
from autosportlabs.uix.bettertextinput import BetterTextInput


CONFIG_VIEW = '''
<AdvancedBluetoothConfigView>
    Label:
        text: "NOTE: current values not shown. Enter new values to change settings. Changes will take affect after restarting RaceCapture."
        text_size: root.width, None
        size_hint_y: None
        height: self.texture_size[1]
        padding: [dp(10), dp(10)]
    GridLayout:
        cols: 1
        spacing: dp(10)
        SettingsView:
            id: name
            label_text: 'New Name'
            help_text: 'Minimum 1 character'
        SettingsView:
            id: passkey
            label_text: 'New Passcode'
            help_text: '4 digits required'
'''


class AdvancedBluetoothConfigView(StackLayout):
    """
    Advanced Bluetooth configuration for name and passkey. For RCP Mk2, the configuration cannot be read and new
    configuration will take affect after a power cycle.

    Only alphanumerics are allowed for name and 4 digits for the passkey is required
    """
    Builder.load_string(CONFIG_VIEW)

    def __init__(self, config, **kwargs):
        self.config = config
        self.valid = True
        super(AdvancedBluetoothConfigView, self).__init__(**kwargs)

        self.ids.passkey.setControl(BetterTextInput(max_chars=4, regex='\D'))
        self.ids.name.setControl(BetterTextInput(max_chars=14, regex='\W'))

    def validate(self):
        """
        Validates the fields, sets errors where appropriate
        :return: Boolean valid
        """
        valid = True

        passkey = self.ids.passkey.control.text

        if 0 < len(passkey) < 4:
            self.ids.passkey.set_error("Passcode must be 4 digits")
            valid = False

        return valid

    @property
    def values(self):
        """
        Returns all field values
        :return: Dict a dictionary of the fields
        """
        values = {
            "passkey": self.ids.passkey.control.text,
            "name": self.ids.name.control.text
        }

        return values
