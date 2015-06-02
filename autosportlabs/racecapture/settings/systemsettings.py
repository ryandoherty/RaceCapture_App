from autosportlabs.racecapture.data.channels import SystemChannels, RuntimeChannels
from autosportlabs.racecapture.settings.appconfig import AppConfig
from autosportlabs.racecapture.settings.prefs import UserPrefs


class SystemSettings(object):
    def __init__(self, data_dir, base_dir = None):
        self.systemChannels = SystemChannels(base_dir=base_dir)
        self.runtimeChannels = RuntimeChannels(system_channels=self.systemChannels)        
        self.userPrefs = UserPrefs(data_dir)
        self.appConfig = AppConfig()
