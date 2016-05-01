from autosportlabs.racecapture.data.channels import SystemChannels, RuntimeChannels
from autosportlabs.racecapture.settings.appconfig import AppConfig
from autosportlabs.racecapture.settings.prefs import UserPrefs
from kivy.utils import platform
from os.path import dirname, expanduser, sep
from os import path

class SettingsListener(object):
    '''
    Base class for listining to changes in settings / preferences
    '''

    def settings_updated(self, settings):
        '''
        Notify if settings have been updated
        :param settings the settings object
        :type settings SystemSettings
        '''
        pass

    def user_preferences_updated(self, user_prefs):
        '''
        Notify if user preferences have changed
        :param user_prefs user preferences
        :type UserPrefs
        '''
        pass

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
            from jnius import autoclass
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            activity = PythonActivity.mActivity
            return activity.getExternalFilesDir(None).getPath()
        else:
            return self.data_dir

    def get_default_user_files_dir(self):
        if platform() == 'android':
            from jnius import autoclass
            env = autoclass('android.os.Environment')
            return path.join(env.getExternalStorageDirectory().getPath(), 'racecapture')
        else:
            return self.get_default_desktop_config_dir()

    def get_default_desktop_config_dir(self):
        if platform() == 'win':
            return path.join(dirname(expanduser('~')), 'Documents')
        else:
            return path.join(expanduser('~'), 'Documents')


