from autosportlabs.racecapture.data.sampledata import SystemChannels, RuntimeChannels
from autosportlabs.racecapture.settings.appconfig import AppConfig
from autosportlabs.racecapture.settings.prefs import UserPrefs
from kivy.utils import platform
from os.path import dirname, expanduser
from os import path

class SystemSettings(object):
    def __init__(self, base_dir = None):
        self.systemChannels = SystemChannels(base_dir=base_dir)
        self.runtimeChannels = RuntimeChannels(system_channels=self.systemChannels)        
        self.userPrefs = UserPrefs(data_dir=SystemSettings.get_default_data_dir(), 
                                   user_files_dir=SystemSettings.get_default_user_files_dir())
        self.appConfig = AppConfig()

    @staticmethod    
    def get_default_data_dir():
        if platform() == 'android':
            from jnius import autoclass
            env = autoclass('android.os.Environment')
            return env.getDataDirectory().getPath() 
        else:
            return SystemSettings.get_default_desktop_config_dir()
        
    @staticmethod            
    def get_default_user_files_dir():
        if platform() == 'android':
            from jnius import autoclass
            env = autoclass('android.os.Environment')
            return env.getExternalStorageDirectory().getPath() 
        else:
            return SystemSettings.get_default_desktop_config_dir()

    @staticmethod
    def get_default_desktop_config_dir():
        if platform() == 'win':
            return path.join(dirname(expanduser('~')), 'Documents')
        else:
            return path.join(expanduser('~'), 'Documents')

        