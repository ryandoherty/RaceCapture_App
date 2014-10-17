from autosportlabs.racecapture.data.sampledata import SystemChannels
from autosportlabs.racecapture.settings.appconfig import AppConfig
from autosportlabs.racecapture.settings.prefs import UserPrefs
 
class SystemSettings(object):
	systemChannels = SystemChannels()
	userPrefs = UserPrefs()
	appConfig = AppConfig()
	
	