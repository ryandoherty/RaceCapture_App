import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.settings import SettingsWithNoMenu
from kivy.app import Builder
from utils import *
import os

Builder.load_file('autosportlabs/racecapture/views/preferences/preferences.kv')

class PreferencesView(Screen):
    settings = None
    content = None

    def __init__(self, settings, **kwargs):
        super(PreferencesView, self).__init__(**kwargs)
        self.settings = settings

        settings_view = SettingsWithNoMenu()
        settings_view.add_json_panel('Preferences', self.settings.userPrefs.config, os.path.join(os.getcwd(), 'resource', 'settings', 'settings.json'))

        self.content = kvFind(self, 'rcid', 'preferences')
        self.content.add_widget(settings_view)
