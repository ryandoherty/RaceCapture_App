import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.logger import Logger
import os, json
from utils import *
from settingsview import SettingsSwitch, SettingsMappedSpinner

CELLULAR_CONFIG_VIEW = 'autosportlabs/racecapture/views/configuration/rcp/wireless/cellularconfigview.kv'


class CellularConfigView(GridLayout):

    def __init__(self, base_dir, config, **kwargs):
        Builder.load_file(CELLULAR_CONFIG_VIEW)
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
        Logger.info("CellularConfig: got new config: {}".format(rcpCfg.connectivityConfig.cellConfig.toJson()))

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
            Logger.info("CellularConfig: existing apn name: {}".format(existingApnName))
            self.apnSpinner.text = existingApnName

        self.connectivityConfig = rcpCfg.connectivityConfig

    def on_modified(self):
        pass
