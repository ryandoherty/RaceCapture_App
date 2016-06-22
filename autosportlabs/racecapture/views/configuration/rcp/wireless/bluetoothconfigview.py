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
