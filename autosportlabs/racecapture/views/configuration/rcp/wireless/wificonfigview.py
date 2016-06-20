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

    def __init__(self, base_dir, config, **kwargs):
        Builder.load_file(WIFI_CONFIG_VIEW)
        super(WifiConfigView, self).__init__(**kwargs)
        self.wifi_config = config.wifi_config if config else None
        self.base_dir = base_dir

        self.register_event_type('on_modified')
        self.config_updated(config)

    def on_ap_channel(self, instance, value):
        Logger.debug("WirelessConfigView: got new AP channel: {}".format(value))
        if self.wifi_config:
            self.wifi_config.ap_channel = int(value)
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_encryption(self, instance, value):
        Logger.debug("WirelessConfigView: got new AP encryption: {}".format(value))
        if self.wifi_config:
            self.wifi_config.ap_encryption = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_ssid(self, instance, value):
        Logger.debug("WirelessConfigView: got new client ssid: {}".format(value))
        if self.wifi_config:
            self.wifi_config.client_ssid = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_password(self, instance, value):
        Logger.debug("WirelessConfigView: got new ap password: {}".format(value))
        if self.wifi_config:
            self.wifi_config.ap_password = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_ssid(self, instance, value):
        Logger.debug("WirelessConfigView: got new ap ssid: {}".format(value))
        if self.wifi_config:
            self.wifi_config.ap_ssid = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_password(self, instance, value):
        Logger.debug("WirelessConfigView: got new client pass: {}".format(value))
        if self.wifi_config:
            self.wifi_config.client_password = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_mode_enable_change(self, instance, value):
        Logger.debug("WirelessConfigView: ap mode change: {}".format(value))
        if self.wifi_config:
            self.wifi_config.ap_mode_active = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_mode_enable_change(self, instance, value):
        Logger.debug("WirelessConfigView: client mode change: {}".format(value))
        if self.wifi_config:
            self.wifi_config.client_mode_active = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_wifi_enable_change(self, instance, value):
        Logger.debug("WifiConfigView: got wifi enabled change")
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

    def config_updated(self, config):

        wifi_config = config.wifi_config
        Logger.debug("WifiConfig: got config: {}".format(wifi_config.to_json()))

        wifi_switch = self.ids.wifi_enabled
        wifi_switch.setControl(SettingsSwitch(active=wifi_config.active))
        wifi_switch.control.bind(active=self.on_wifi_enable_change)

        wifi_client_switch = self.ids.client_mode
        wifi_client_switch.setControl(SettingsSwitch(active=wifi_config.client_mode_active))
        wifi_client_switch.control.bind(active=self.on_client_mode_enable_change)

        wifi_ap_switch = self.ids.ap_mode
        wifi_ap_switch.setControl(SettingsSwitch(active=wifi_config.ap_mode_active))
        wifi_ap_switch.control.bind(active=self.on_ap_mode_enable_change)

        ap_encryption = self.ids.ap_encryption
        ap_encryption.bind(on_setting=self.on_ap_encryption)
        encryption_spinner = SettingsMappedSpinner()
        self.load_ap_encryption_spinner(encryption_spinner)
        ap_encryption.setControl(encryption_spinner)

        if wifi_config.ap_encryption != "":
            self.ids.ap_encryption.setValue(wifi_config.ap_encryption)

        ap_channel = self.ids.ap_channel
        ap_channel.bind(on_setting=self.on_ap_channel)
        channel_spinner = SettingsMappedSpinner()
        self.build_ap_channel_spinner(channel_spinner)
        ap_channel.setControl(channel_spinner)

        if wifi_config.ap_channel:
            self.ids.ap_channel.setValue(str(wifi_config.ap_channel))

        self.ids.client_ssid.text = wifi_config.client_ssid
        self.ids.client_password.text = wifi_config.client_password

        self.ids.ap_ssid.text = wifi_config.ap_ssid
        self.ids.ap_password.text = wifi_config.ap_password

        self.wifi_config = wifi_config

    def on_modified(self):
        pass
