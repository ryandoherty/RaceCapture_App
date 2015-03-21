from autosportlabs.racecapture.data.sampledata import SystemChannels
from autosportlabs.racecapture.settings.appconfig import AppConfig
from autosportlabs.racecapture.settings.prefs import UserPrefs


class SystemSettings(object):
    def __init__(self, data_dir, base_dir = None):
        self.systemChannels = SystemChannels(base_dir=base_dir)
        self.userPrefs = UserPrefs(data_dir)
        self.appConfig = AppConfig()
