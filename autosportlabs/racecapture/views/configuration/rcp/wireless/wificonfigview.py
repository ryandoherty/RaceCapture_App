import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.logger import Logger
import os, json
from settingsview import SettingsView, SettingsSwitch, SettingsButton, SettingsMappedSpinner
from autosportlabs.uix.bettertextinput import BetterTextInput

WIFI_CONFIG_VIEW = 'autosportlabs/racecapture/views/configuration/rcp/wireless/wificonfigview.kv'


class WifiConfigView(GridLayout):

    def __init__(self, base_dir, **kwargs):
        Builder.load_file(WIFI_CONFIG_VIEW)
        super(WifiConfigView, self).__init__(**kwargs)
        self.wifi_config = None
        self.base_dir = base_dir

        self.register_event_type('on_modified')

        wifi_switch = self.ids.wifi_enabled
        wifi_switch.setControl(SettingsSwitch())
        wifi_switch.control.bind(on_value=self.on_wifi_enable_change)

        wifi_client_switch = self.ids.client_mode
        wifi_client_switch.setControl(SettingsSwitch())
        wifi_client_switch.control.bind(on_value=self.on_client_mode_enable_change)

        wifi_ap_switch = self.ids.ap_mode
        wifi_ap_switch.setControl(SettingsSwitch())
        wifi_ap_switch.control.bind(on_value=self.on_ap_mode_enable_change)

        ap_encryption = self.ids.ap_encryption
        ap_encryption.bind(on_setting=self.on_ap_encryption)
        encryption_spinner = SettingsMappedSpinner()
        self.load_ap_encryption_spinner(encryption_spinner)
        ap_encryption.setControl(encryption_spinner)

        ap_channel = self.ids.ap_channel
        ap_channel.bind(on_setting=self.on_ap_channel)
        channel_spinner = SettingsMappedSpinner()
        self.build_ap_channel_spinner(channel_spinner)
        ap_channel.setControl(channel_spinner)

    def on_ap_channel(self, instance, value):
        if self.wifi_config:
            self.wifi_config.ap_channel = int(value)
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_encryption(self, instance, value):
        Logger.info("WirelessConfigView: got new AP encryption: {}".format(value))
        if self.wifi_config:
            self.wifi_config.ap_encryption = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_ssid(self, instance, value):
        if self.wifi_config:
            self.wifi_config.client_ssid = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_password(self, instance, value):
        if self.wifi_config:
            self.wifi_config.ap_password = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_ssid(self, instance, value):
        if self.wifi_config:
            self.wifi_config.ap_ssid = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_password(self, instance, value):
        if self.wifi_config:
            self.wifi_config.client_password = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_mode_enable_change(self, instance, value):
        if self.wifi_config:
            self.wifi_config.ap_mode_active = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_mode_enable_change(self, instance, value):
        if self.wifi_config:
            self.wifi_config.client_mode_active = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_wifi_enable_change(self, instance, value):
        if self.wifi_config:
            self.wifi_config.active = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def build_ap_channel_spinner(self, spinner):
        channel_map = {}

        for i in range(1, 12, 1):
            i = str(i)
            channel_map[i] = i

        spinner.setValueMap(channel_map, "1", sort_key=lambda value: int(value))

    def load_ap_encryption_spinner(self, spinner):
        json_data = open(os.path.join(self.base_dir, 'resource', 'settings', 'ap_encryption.json'))
        encryption_json = json.load(json_data)

        spinner.setValueMap(encryption_json['types'], 'WPA2')

    def config_updated(self, rcpCfg):

        wifi_config = rcpCfg.wifi_config

        self.ids.wifi_enabled.setValue(wifi_config.active)

        self.ids.client_mode.setValue(wifi_config.client_mode_active)
        self.ids.client_ssid.text = wifi_config.client_ssid
        self.ids.client_password.text = wifi_config.client_password

        self.ids.ap_mode.setValue(wifi_config.ap_mode_active)
        self.ids.ap_ssid.text = wifi_config.ap_ssid
        self.ids.ap_password.text = wifi_config.ap_password

        if wifi_config.ap_encryption != "":
            self.ids.ap_encryption.setValue(wifi_config.ap_encryption)

        if wifi_config.ap_channel:
            self.ids.ap_channel.setValue(str(wifi_config.ap_channel))

        self.wifi_config = wifi_config

    def on_modified(self):
        pass
