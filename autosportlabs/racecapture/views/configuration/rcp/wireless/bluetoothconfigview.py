import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.logger import Logger
from settingsview import SettingsView, SettingsSwitch, SettingsButton
from autosportlabs.widgets.separator import HLineSeparator
from autosportlabs.racecapture.views.util.alertview import editor_popup
from autosportlabs.racecapture.views.configuration.rcp.advancedbluetoothconfigview import AdvancedBluetoothConfigView

Builder.load_string('''
<BluetoothConfigView>
    id: bluetooth
    cols: 1
    spacing: [0, dp(20)]
    size_hint: [1, None]
    height: self.minimum_height
    HSeparator:
        text: 'Bluetooth'
        size_hint_y: None
    SettingsView:
        id: bt_enable
        label_text: 'Bluetooth'
        help_text: 'If the Bluetooth module is connected, enable it here'
    SettingsView:
        id: btconfig
        label_text: 'Advanced configuration'
        help_text: 'Change Bluetooth name and passkey. Firmware version 2.9.0 or greater required.'
''')


class BluetoothConfigView(GridLayout):

    def __init__(self, config, **kwargs):
        super(BluetoothConfigView, self).__init__(**kwargs)

        self.config = None
        self.register_event_type('on_modified')

        self.config_updated(config)
        self._bt_popup = None
        self._bt_config_view = None

        btConfig = self.ids.btconfig
        btConfig.bind(on_setting=self.on_bt_configure)
        btConfig.setControl(SettingsButton(text='Advanced'))

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

    def on_bt_configure(self, instance, value):
        if not self._bt_popup:
            content = AdvancedBluetoothConfigView(self.config.connectivityConfig)
            popup = editor_popup(title="Configure Bluetooth", content=content,
                                 answerCallback=self.on_bluetooth_popup_answer)
            self._bt_popup = popup
            self._bt_config_view = content

    def on_bluetooth_popup_answer(self, instance, answer):
        close = True
        modified = False

        # If the user clicked the checkbox to save, validate the view. If it's valid, close and save values to config.
        # If invalid, leave it (view will show error messages)
        if answer:
            valid = self._bt_config_view.validate()

            if valid:
                bt_values = self._bt_config_view.values

                if len(bt_values["name"]) > 0:
                    self.config.connectivityConfig.bluetoothConfig.name = bt_values["name"]
                    modified = True

                if len(bt_values["passkey"]) > 0:
                    self.config.connectivityConfig.bluetoothConfig.passKey = bt_values["passkey"]
                    modified = True
            else:
                close = False

        if modified:
            self.config.connectivityConfig.stale = True
            self.dispatch('on_modified')

        if close:
            self._bt_popup.dismiss()
            self._bt_popup = None
            self._bt_config_view = None

