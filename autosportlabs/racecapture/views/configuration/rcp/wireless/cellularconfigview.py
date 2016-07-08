import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.logger import Logger
import os
import json
from utils import *
from settingsview import SettingsSwitch, SettingsMappedSpinner

Builder.load_string('''
<CellularConfigView>:
    id: cellular
    cols: 1
    spacing: [0, dp(20)]
    row_default_height: dp(40)
    size_hint: [1, None]
    height: self.minimum_height
    HSeparator:
        text: 'Cellular Configuration'
    SettingsView:
        size_hint_y: 0.20
        rcid: 'cellEnable'
        label_text: 'Cellular Module'
        help_text: 'Enable if the Real-time telemetry module is installed'
    SettingsView:
        size_hint_y: None
        rcid: 'cellprovider'
        label_text: 'Cellular Provider'
        help_text: 'Select the cellular provider, or specify custom APN settings'
    Label:
        text: 'Custom Cellular Settings'
        text_size: self.size
        halign: 'center'
        font_size: dp(26)
    GridLayout:
        cols: 2
        spacing: (dp(30), dp(5))
        FieldLabel:
            text: 'APN Host'
            halign: 'right'
        ValueField:
            rcid: 'apnHost'
            disabled: True
            on_text: root.on_apn_host(*args)
    GridLayout:
        cols: 2
        spacing: (dp(30), dp(5))
        FieldLabel:
            halign: 'right'
            text: 'APN User Name'
        ValueField:
            rcid: 'apnUser'
            size_hint_y: 1
            disabled: True
            on_text: root.on_apn_user(*args)
    GridLayout:
        cols: 2
        spacing: (dp(30), dp(5))
        FieldLabel:
            halign: 'right'
            text: 'APN Password'
        ValueField:
            rcid: 'apnPass'
            disabled: True
            size_hint_y: 1
            on_text: root.on_apn_pass(*args)
''')


class CellularConfigView(GridLayout):

    def __init__(self, base_dir, config, **kwargs):
        super(CellularConfigView, self).__init__(**kwargs)
        self.connectivityConfig = None
        self.base_dir = base_dir
        self.customApnLabel = 'Custom APN'
        self.register_event_type('on_modified')
        self.apnSpinner = None

        self.apnHostField = kvFind(self, 'rcid', 'apnHost')
        self.apnUserField = kvFind(self, 'rcid', 'apnUser')
        self.apnPassField = kvFind(self, 'rcid', 'apnPass')

        self.config_updated(config)

    def setCustomApnFieldsDisabled(self, disabled):
        self.apnHostField.disabled = disabled
        self.apnUserField.disabled = disabled
        self.apnPassField.disabled = disabled

    def on_apn_host(self, instance, value):
        if self.connectivityConfig:
            Logger.info("CellularConfigView: got new apn host")
            self.connectivityConfig.cellConfig.apnHost = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')

    def on_apn_user(self, instance, value):
        if self.connectivityConfig and value != self.connectivityConfig.cellConfig.apnUser:
            Logger.info("CellularConfigView: got new apn user")
            self.connectivityConfig.cellConfig.apnUser = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')

    def on_apn_pass(self, instance, value):
        if self.connectivityConfig and value != self.connectivityConfig.cellConfig.apnPass:
            Logger.info("CellularConfigView: got new apn pass")
            self.connectivityConfig.cellConfig.apnPass = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')

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

    def getApnSettingByName(self, name):
        providers = self.cellProviderInfo['cellProviders']
        for apnName in providers:
            if apnName == name:
                return providers[apnName]
        return None

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

    def on_cell_change(self, instance, value):
        if self.connectivityConfig:
            Logger.info("CellularConfigView: got new cell enabled change")
            self.connectivityConfig.cellConfig.cellEnabled = value
            self.connectivityConfig.stale = True
            self.dispatch('on_modified')

    def update_controls_state(self):
        if self.connectivityConfig:
            cellProviderInfo = self.cellProviderInfo
            existingApnName = self.customApnLabel
            customFieldsDisabled = False
            cellConfig = self.connectivityConfig.cellConfig
            providers = cellProviderInfo['cellProviders']
            for name in providers:
                apnInfo = providers[name]
                if apnInfo['apn_host'] == cellConfig.apnHost and apnInfo['apn_user'] == cellConfig.apnUser and apnInfo['apn_pass'] == cellConfig.apnPass:
                    existingApnName = name
                    customFieldsDisabled = True
                    break
            self.setCustomApnFieldsDisabled(customFieldsDisabled)
            return existingApnName

    def config_updated(self, rcpCfg):

        cellEnable = kvFind(self, 'rcid', 'cellEnable')
        cellEnable.setControl(SettingsSwitch(active=rcpCfg.connectivityConfig.cellConfig.cellEnabled))
        cellEnable.control.bind(active=self.on_cell_change)

        cellProvider = kvFind(self, 'rcid', 'cellprovider')
        cellProvider.bind(on_setting=self.on_cell_provider)
        apnSpinner = SettingsMappedSpinner()

        self.loadApnSettingsSpinner(apnSpinner)
        self.apnSpinner = apnSpinner
        cellProvider.setControl(apnSpinner)

        self.apnHostField.text = rcpCfg.connectivityConfig.cellConfig.apnHost
        self.apnUserField.text = rcpCfg.connectivityConfig.cellConfig.apnUser
        self.apnPassField.text = rcpCfg.connectivityConfig.cellConfig.apnPass

        existingApnName = self.update_controls_state()
        if existingApnName:
            self.apnSpinner.text = existingApnName

        self.connectivityConfig = rcpCfg.connectivityConfig

    def on_modified(self):
        pass
