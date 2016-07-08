import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.logger import Logger
import os, json
from settingsview import SettingsView, SettingsSwitch, SettingsButton, SettingsMappedSpinner
from autosportlabs.uix.bettertextinput import BetterTextInput
from autosportlabs.uix.baselabel import BaseLabel

Builder.load_string('''

<WifiConfigView>:
    id: wifi
    cols: 1
    spacing: [0, dp(20)]
    row_default_height: dp(40)
    size_hint: [1, None]
    height: self.minimum_height
    HSeparator:
        text: 'WiFi'
    SettingsView:
        id: wifi_enabled
        label_text: 'WiFi Module'
    BaseLabel:
        text_size: self.size
        halign: 'center'
        text: 'Client Mode Configuration'
        font_size: dp(26)
    BaseLabel:
        text: 'Use this mode to setup the wifi module to connect [b]to[/b] an existing wireless network.'
        markup: True
        text_size: (self.parent.width, None)
        padding: [dp(20), 0]
    SettingsView:
        id: client_mode
        label_text: 'Client Mode'
    GridLayout:
        spacing: (dp(30), dp(5))
        cols: 2
        FieldLabel:
            text: 'SSID'
            halign: 'right'
        ValueField:
            id: client_ssid
            disabled: False
            on_text: root.on_client_ssid(*args)
    GridLayout:
        spacing: (dp(30), dp(5))
        cols: 2
        FieldLabel:
            text: 'Password'
            halign: 'right'
        ValueField:
            id: client_password
            disabled: False
            on_text: root.on_client_password(*args)
    BaseLabel:
        text: 'Access Point Mode Configuration'
        text_size: self.size
        halign: 'center'
        font_size: dp(26)
    BaseLabel:
        text: 'Use this mode to create a wireless network for your phone or table to connect to.'
        markup: True
        text_size: (self.parent.width, None)
        padding: [dp(20), 0]
    SettingsView:
        id: ap_mode
        label_text: 'Access Point Mode'
    GridLayout:
        spacing: (dp(30), dp(5))
        cols: 2
        FieldLabel:
            text: 'SSID'
            halign: 'right'
        BetterTextInput:
            id: ap_ssid
            disabled: False
            on_text: root.on_ap_ssid(*args)
            max_chars: 24
    GridLayout:
        spacing: (dp(30), dp(5))
        cols: 2
        FieldLabel:
            text: 'Password'
            halign: 'right'
        BetterTextInput:
            id: ap_password
            disabled: False
            on_text: root.on_ap_password(*args)
            max_chars: 24
    SettingsView:
        id: ap_channel
        label_text: 'Channel'
    SettingsView:
        id: ap_encryption
        label_text: 'Encryption'
''')


class WifiConfigView(GridLayout):

    def __init__(self, base_dir, config, **kwargs):
        super(WifiConfigView, self).__init__(**kwargs)
        self.wifi_config = config.wifi_config if config else None
        self.base_dir = base_dir

        self.register_event_type('on_modified')

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
        if self.wifi_config and value != self.wifi_config.client_ssid:
            Logger.debug("WirelessConfigView: got new client ssid: {}".format(value))
            self.wifi_config.client_ssid = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_password(self, instance, value):
        if self.wifi_config and value != self.wifi_config.ap_password:
            Logger.debug("WirelessConfigView: got new ap password: {}".format(value))
            self.wifi_config.ap_password = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_ap_ssid(self, instance, value):
        if self.wifi_config and value != self.wifi_config.ap_ssid:
            Logger.debug("WirelessConfigView: got new ap ssid: {}".format(value))
            self.wifi_config.ap_ssid = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_password(self, instance, value):
        if self.wifi_config and value != self.wifi_config.client_password:
            Logger.debug("WirelessConfigView: got new client pass: {}".format(value))
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

    def build_ap_channel_spinner(self, spinner, default=1):
        channel_map = {}

        for i in range(1, 12, 1):
            i = str(i)
            channel_map[i] = i

        spinner.setValueMap(channel_map, str(default), sort_key=lambda value: int(value))

    def load_ap_encryption_spinner(self, spinner, default="WPA2"):
        json_data = open(os.path.join(self.base_dir, 'resource', 'settings', 'ap_encryption.json'))
        encryption_json = json.load(json_data)

        if default in encryption_json['types']:
            default = encryption_json['types'][default]

        spinner.setValueMap(encryption_json['types'], default)

    def config_updated(self, config):

        self.wifi_config = config.wifi_config
        Logger.debug("WifiConfig: got config: {}".format(self.wifi_config.to_json()))

        wifi_switch = self.ids.wifi_enabled
        wifi_switch.setControl(SettingsSwitch(active=self.wifi_config.active))
        wifi_switch.control.bind(active=self.on_wifi_enable_change)

        wifi_client_switch = self.ids.client_mode
        wifi_client_switch.setControl(SettingsSwitch(active=self.wifi_config.client_mode_active))
        wifi_client_switch.control.bind(active=self.on_client_mode_enable_change)

        wifi_ap_switch = self.ids.ap_mode
        wifi_ap_switch.setControl(SettingsSwitch(active=self.wifi_config.ap_mode_active))
        wifi_ap_switch.control.bind(active=self.on_ap_mode_enable_change)

        ap_encryption = self.ids.ap_encryption
        ap_encryption.bind(on_setting=self.on_ap_encryption)
        encryption_spinner = SettingsMappedSpinner()
        self.load_ap_encryption_spinner(encryption_spinner, self.wifi_config.ap_encryption)
        ap_encryption.setControl(encryption_spinner)

        ap_channel = self.ids.ap_channel
        channel_spinner = SettingsMappedSpinner()
        self.build_ap_channel_spinner(channel_spinner, str(self.wifi_config.ap_channel))
        ap_channel.bind(on_setting=self.on_ap_channel)
        ap_channel.setControl(channel_spinner)

        self.ids.client_ssid.text = self.wifi_config.client_ssid
        self.ids.client_password.text = self.wifi_config.client_password

        self.ids.ap_ssid.text = self.wifi_config.ap_ssid
        self.ids.ap_password.text = self.wifi_config.ap_password

    def on_modified(self):
        pass
