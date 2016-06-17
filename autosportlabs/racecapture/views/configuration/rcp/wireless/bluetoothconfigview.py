import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.logger import Logger
from settingsview import SettingsView,SettingsSwitch
from autosportlabs.widgets.separator import HLineSeparator

BLUETOOTH_CONFIG_VIEW = 'autosportlabs/racecapture/views/configuration/rcp/wireless/bluetoothconfigview.kv'


class BluetoothConfigView(GridLayout):

    def __init__(self, config, **kwargs):
        Builder.load_file(BLUETOOTH_CONFIG_VIEW)
        super(BluetoothConfigView, self).__init__(**kwargs)

        self.register_event_type('on_modified')

        bluetooth_enabled = self.ids.bt_enable
        bluetooth_enabled.bind(on_setting=self.on_bluetooth_enable)
        bluetooth_enabled.setControl(SettingsSwitch())

        self.config = config

    def on_bluetooth_enable(self, instance, value):
        Logger.info("BluetoothConfigView: on_bluetooth_enable")
        if value == self.config.connectivityConfig.bluetoothConfig.btEnabled:
            return
        if self.config and self.config.connectivityConfig:
            self.config.connectivityConfig.bluetoothConfig.btEnabled = value
            self.config.connectivityConfig.stale = True
            self.dispatch('on_modified')

    def config_updated(self, config):
        Logger.info("BluetoothConfigView: config_updated")
        self.config = config
        self.ids.bt_enable.value = self.config.connectivityConfig.bluetoothConfig.btEnabled

    def on_modified(self):
        pass
