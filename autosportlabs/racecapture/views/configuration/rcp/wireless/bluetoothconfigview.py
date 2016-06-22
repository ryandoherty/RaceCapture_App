import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.logger import Logger
from settingsview import SettingsView,SettingsSwitch
from autosportlabs.widgets.separator import HLineSeparator

Builder.load_string('''
<BluetoothConfigView>
    id: bluetooth
    cols: 1
    spacing: [0, dp(20)]
    row_default_height: dp(40)
    size_hint: [1, None]
    height: self.minimum_height
    HSeparator:
        size_hint_y: 0.5
        text: 'Bluetooth'
    SettingsView:
        id: bt_enable
        label_text: 'Bluetooth'
        help_text: 'If the Bluetooth module is connected, enable it here'
        size_hint_y: 1
''')


class BluetoothConfigView(GridLayout):

    def __init__(self, config, **kwargs):
        super(BluetoothConfigView, self).__init__(**kwargs)

        self.config = None
        self.register_event_type('on_modified')

        self.config_updated(config)

    def on_bluetooth_enabled_change(self, instance, value):
        if self.config:
            self.config.connectivityConfig.bluetoothConfig.btEnabled = value
            self.config.connectivityConfig.stale = True
            self.dispatch('on_modified')

    def config_updated(self, config):
        self.config = config

        value = self.config.connectivityConfig.bluetoothConfig.btEnabled

        bluetooth_enabled = self.ids.bt_enable
        bluetooth_enabled.setControl(SettingsSwitch(active=value))
        bluetooth_enabled.control.bind(active=self.on_bluetooth_enabled_change)

    def on_modified(self):
        pass
