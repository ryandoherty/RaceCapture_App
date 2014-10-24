import unittest
import os
from autosportlabs.racecapture.settings.prefs import UserPrefs

class UserPrefsTest(unittest.TestCase):
    data_dir = os.getcwd()

    def setUp(self):
       self.user_prefs = UserPrefs(data_dir=self.data_dir)

    def test_set_range_alert(self):
        self.user_prefs.set_range_alert('foo', 'bar')
        self.assertEquals(self.user_prefs._prefs_dict['range_alerts']['foo'], 'bar')
