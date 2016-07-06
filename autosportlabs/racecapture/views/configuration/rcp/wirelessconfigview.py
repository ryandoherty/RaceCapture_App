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
import os
from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.logger import Logger
import json
from settingsview import SettingsView, SettingsSwitch, SettingsButton, SettingsMappedSpinner
from autosportlabs.widgets.separator import HLineSeparator
from valuefield import ValueField
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.views.configuration.rcp.bluetoothconfigview import BluetoothConfigView
from autosportlabs.racecapture.views.util.alertview import editor_popup

WIRELESS_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/wirelessconfigview.kv'

class WirelessConfigView(BaseConfigView):
    customApnLabel = 'Custom APN'
    apnSpinner = None
    cellProviderInfo = None
    connectivityConfig = None
    apnHostField = None
    apnUserField = None
    apnPassField = None
    base_dir = None
    
    def __init__(self, **kwargs):
        Builder.load_file(WIRELESS_CONFIG_VIEW_KV)
        super(WirelessConfigView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.base_dir = kwargs.get('base_dir')

        btEnable = kvFind(self, 'rcid', 'btEnable') 
        btEnable.bind(on_setting=self.on_bt_enable)
        btEnable.setControl(SettingsSwitch())
        
        btConfig = self.ids.btconfig
        btConfig.bind(on_setting=self.on_bt_configure)
        btConfig.setControl(SettingsButton(text='Advanced'))
        
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

        self._bt_popup = None
        self._bt_config_view = None

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
        if not self._bt_popup:
            content = BluetoothConfigView(self.connectivityConfig)
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
                    self.connectivityConfig.bluetoothConfig.name = bt_values["name"]
                    modified = True

                if len(bt_values["passkey"]) > 0:
                    self.connectivityConfig.bluetoothConfig.passKey = bt_values["passkey"]
                    modified = True
            else:
                close = False

        if modified:
            Logger.info("WirelessConfigView: BT config modified: {}".format(self.connectivityConfig.bluetoothConfig.toJson()))
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')

        if close:
            self._bt_popup.dismiss()
            self._bt_popup = None
            self._bt_config_view = None

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
