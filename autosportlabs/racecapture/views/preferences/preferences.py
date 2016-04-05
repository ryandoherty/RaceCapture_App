import kivy
kivy.require('1.9.1')

from kivy.uix.boxlayout import BoxLayout
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.settings import SettingsWithNoMenu
from kivy.app import Builder
from utils import *
import os

PREFERENCES_KV_FILE = 'autosportlabs/racecapture/views/preferences/preferences.kv'

class PreferencesView(Screen):
    settings = None
    content = None
    base_dir = None

    def __init__(self, settings, **kwargs):
        Builder.load_file(PREFERENCES_KV_FILE)
        super(PreferencesView, self).__init__(**kwargs)
        self.settings = settings
        self.base_dir = kwargs.get('base_dir')

        self.settings_view = SettingsWithNoMenu()
        self.settings_view.add_json_panel('Preferences', self.settings.userPrefs.config, os.path.join(self.base_dir, 'resource', 'settings', 'settings.json'))

        self.content = kvFind(self, 'rcid', 'preferences')
        self.content.add_widget(self.settings_view)
