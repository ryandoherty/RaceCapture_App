import kivy
kivy.require('1.9.1')
import os
from kivy.app import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import json
from settingsview import SettingsView, SettingsSwitch, SettingsButton, SettingsMappedSpinner
from autosportlabs.widgets.separator import HLineSeparator
from valuefield import ValueField
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from kivy.modules import inspector
from kivy.logger import Logger

WIRELESS_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/wirelessconfigview.kv'

class WirelessConfigView(BaseConfigView):
    customApnLabel = 'Custom APN'
    apnSpinner = None
    cellProviderInfo = None
    connectivityConfig = None
    wifi_config = None
    apnHostField = None
    apnUserField = None
    apnPassField = None
    base_dir = None
    
    def __init__(self, **kwargs):
        Builder.load_file(WIRELESS_CONFIG_VIEW_KV)
        super(WirelessConfigView, self).__init__(**kwargs)
        inspector.create_inspector(Window, self)
        self.register_event_type('on_config_updated')
        self.base_dir = kwargs.get('base_dir')

        btEnable = kvFind(self, 'rcid', 'btEnable')
        btEnable.bind(on_setting=self.on_bt_enable)
        btEnable.setControl(SettingsSwitch())

        wifi_switch = self.ids.wifi_enabled
        wifi_switch.bind(on_setting=self.on_wifi_enable)
        wifi_switch.setControl(SettingsSwitch())

        wifi_client_switch = self.ids.client_mode
        wifi_client_switch.bind(on_setting=self.on_client_mode_enable)
        wifi_client_switch.setControl(SettingsSwitch())

        wifi_ap_switch = self.ids.ap_mode
        wifi_ap_switch.bind(on_setting=self.on_ap_mode_enable)
        wifi_ap_switch.setControl(SettingsSwitch())

        ap_encryption = self.ids.ap_encryption
        ap_encryption.bind(on_setting=self.on_ap_encryption)
        encryption_spinner = SettingsMappedSpinner()
        self.load_ap_encryption_spinner(encryption_spinner)
        ap_encryption.setControl(encryption_spinner)

        cellEnable = kvFind(self, 'rcid', 'cellEnable')
        cellEnable.bind(on_setting=self.on_cell_enable)
        cellEnable.setControl(SettingsSwitch())

        cellProvider = kvFind(self, 'rcid', 'cellprovider')
        cellProvider.bind(on_setting=self.on_cell_provider)
        apnSpinner = SettingsMappedSpinner()
        self.loadApnSettingsSpinner(apnSpinner)
        self.apnSpinner = apnSpinner
        cellProvider.setControl(apnSpinner)

        self.apnHostField = kvFind(self, 'rcid', 'apnHost')
        self.apnUserField = kvFind(self, 'rcid', 'apnUser')
        self.apnPassField = kvFind(self, 'rcid', 'apnPass')

    def on_ap_encryption(self, instance, value):
        Logger.debug("WirelessConfigView: got new AP encryption: {}".format(value))
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

    def on_ap_mode_enable(self, instance, value):
        if self.wifi_config:
            self.wifi_config.ap_mode_enabled = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_client_mode_enable(self, instance, value):
        if self.wifi_config:
            self.wifi_config.client_mode_enabled = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def on_wifi_enable(self, instance, value):
        if self.wifi_config:
            self.wifi_config.active = value
            self.wifi_config.stale = True
            self.dispatch('on_modified')

    def setCustomApnFieldsDisabled(self, disabled):
        self.apnHostField.disabled = disabled
        self.apnUserField.disabled = disabled
        self.apnPassField.disabled = disabled
        
    def on_cell_provider(self, instance, value):
        apnSetting = self.getApnSettingByName(value)
        knownProvider = False
        if apnSetting:
            self.apnHostField.text = apnSetting['apn_host']
            self.apnUserField.text = apnSetting['apn_user']
            self.apnPassField.text = apnSetting['apn_pass']
            knownProvider = True
            
        self.update_controls_state()
        self.setCustomApnFieldsDisabled(knownProvider)

    def on_cell_enable(self, instance, value):
        if self.connectivityConfig:
            self.connectivityConfig.cellConfig.cellEnabled = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')
                
    def on_bt_configure(self, instance, value):
        pass
    
    def on_bt_enable(self, instance, value):
        if self.connectivityConfig:
            self.connectivityConfig.bluetoothConfig.btEnabled = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')
                        
    def on_apn_host(self, instance, value):
        if self.connectivityConfig:
            self.connectivityConfig.cellConfig.apnHost = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')
                        
    def on_apn_user(self, instance, value):
        if self.connectivityConfig:
            self.connectivityConfig.cellConfig.apnUser = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')
                        
    def on_apn_pass(self, instance, value):
        if self.connectivityConfig:
            self.connectivityConfig.cellConfig.apnPass = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')
                        
    def getApnSettingByName(self, name):
        providers = self.cellProviderInfo['cellProviders']
        for apnName in providers:
            if apnName == name:
                return providers[apnName]
        return None

    def load_ap_encryption_spinner(self, spinner):
        json_data = open(os.path.join(self.base_dir, 'resource', 'settings', 'ap_encryption.json'))
        encryption_json = json.load(json_data)

        encryption_types = {}

        for name in encryption_json['types']:
            encryption_types[encryption_json['types'][name]] = name

        spinner.setValueMap(encryption_types, 'WPA2')

    def loadApnSettingsSpinner(self, spinner):
        try:
            json_data = open(os.path.join(self.base_dir, 'resource', 'settings', 'cell_providers.json'))
            cellProviderInfo = json.load(json_data)
            apnMap = {}
            apnMap['custom'] = self.customApnLabel

            for name in cellProviderInfo['cellProviders']:
                apnMap[name] = name
                    
            spinner.setValueMap(apnMap, self.customApnLabel)
            self.cellProviderInfo = cellProviderInfo
        except Exception as detail:
            print('Error loading cell providers ' + str(detail))
        
    def update_controls_state(self):
        if self.connectivityConfig:
            cellProviderInfo = self.cellProviderInfo
            existingApnName = self.customApnLabel
            customFieldsDisabled = False
            cellConfig = self.connectivityConfig.cellConfig
            providers = cellProviderInfo['cellProviders']
            for name in providers:
                apnInfo = providers[name]
                if  apnInfo['apn_host'] == cellConfig.apnHost and apnInfo['apn_user'] == cellConfig.apnUser and apnInfo['apn_pass'] == cellConfig.apnPass:
                    existingApnName = name
                    customFieldsDisabled = True
                    break
            self.setCustomApnFieldsDisabled(customFieldsDisabled)
            return existingApnName

    def _update_wifi_config(self, rcpCfg):
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
        else:
            self.ids.ap_encryption.setValue("none")

        self.wifi_config = wifi_config

    def on_config_updated(self, rcpCfg):
        connectivityConfig = rcpCfg.connectivityConfig
        
        bluetoothEnabled = connectivityConfig.bluetoothConfig.btEnabled
        cellEnabled = connectivityConfig.cellConfig.cellEnabled

        kvFind(self, 'rcid', 'btEnable').setValue(bluetoothEnabled)
        kvFind(self, 'rcid', 'cellEnable').setValue(cellEnabled)

        self.apnHostField.text = connectivityConfig.cellConfig.apnHost
        self.apnUserField.text = connectivityConfig.cellConfig.apnUser
        self.apnPassField.text = connectivityConfig.cellConfig.apnPass

        self.connectivityConfig = connectivityConfig

        existingApnName = self.update_controls_state()
        if existingApnName:
            self.apnSpinner.text = existingApnName

        self._update_wifi_config(rcpCfg)
