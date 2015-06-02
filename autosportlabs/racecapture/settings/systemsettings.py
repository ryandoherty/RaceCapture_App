from autosportlabs.racecapture.data.sampledata import SystemChannels, RuntimeChannels
from autosportlabs.racecapture.settings.appconfig import AppConfig
from autosportlabs.racecapture.settings.prefs import UserPrefs
from kivy.utils import platform
from os.path import dirname, expanduser, sep
from os import path

class SystemSettings(object):
    data_dir = None
    base_dir = None
    def __init__(self, data_dir, base_dir):
        self.data_dir = data_dir
        self.base_dir = base_dir
        self.systemChannels = SystemChannels(base_dir=base_dir)
        self.runtimeChannels = RuntimeChannels(system_channels=self.systemChannels)        
        self.userPrefs = UserPrefs(data_dir=self.get_default_data_dir(), 
                                   user_files_dir=self.get_default_user_files_dir())
        self.appConfig = AppConfig()

    def get_default_data_dir(self):
        if platform() == 'android':
            #TODO there's a better way to do this via the Android Context,
            # but it's hard to actually get via Kivy
            return self.base_dir #'/data/data/com.autosportlabs.racecapture'
        else:
            return self.data_dir
        
    def get_default_user_files_dir(self):
        if platform() == 'android':
            from jnius import autoclass
            env = autoclass('android.os.Environment')
            return env.getExternalStorageDirectory().getPath() 
        else:
            return self.get_default_desktop_config_dir()

    def get_default_desktop_config_dir(self):
        if platform() == 'win':
            return path.join(dirname(expanduser('~')), 'Documents')
        else:
            return path.join(expanduser('~'), 'Documents')

        