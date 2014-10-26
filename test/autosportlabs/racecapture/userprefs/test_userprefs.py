import unittest
import os
import time
from autosportlabs.racecapture.settings.prefs import UserPrefs
from autosportlabs.racecapture.settings.prefs import Range

class UserPrefsTest(unittest.TestCase):
    data_dir = os.path.dirname(os.path.realpath(__file__))
    userprefs = None

    def setUp(self):
        self.userprefs = UserPrefs(self.data_dir, save_timeout=1000)

    def tearDown(self):
        try:
            os.remove(self.data_dir+'/'+self.userprefs.prefs_file_name)
        except OSError:
            pass

    def test_set_get_range_alert(self):
        test_range = Range(1, 10)
        self.userprefs.set_range_alert('Coolant', test_range)

        fetched_range = self.userprefs.get_range_alert('Coolant')

        self.assertEquals(test_range.min, fetched_range.min,
                          "Saved range and fetched range do not match")

    def test_save_prefs(self):
        coolant_range = Range(1, 10, color=[2, 2, 2, 2])
        rpm_range = Range(100, 10000, color=[3, 3, 3, 3])
        self.userprefs.set_range_alert('Coolant', coolant_range)
        self.userprefs.set_range_alert('RPM', rpm_range)

        self.userprefs.save()

        #Did it create the file in the right location?
        self.assertTrue(os.path.isfile(self.data_dir+'/'+self.userprefs.prefs_file_name))

        newprefs = UserPrefs(self.data_dir, save_timeout=1000)

        #newprefs should load the prefs file
        new_coolant = newprefs.get_range_alert('Coolant')
        new_rpm = newprefs.get_range_alert('RPM')

        self.assertEquals(coolant_range.min,
                          new_coolant.min,
                          "Range min not saved and loaded from prefs file")
        self.assertEquals(coolant_range.max,
                          new_coolant.max,
                          "Range max not saved and loaded from prefs file")
        self.assertEquals(coolant_range.color,
                          new_coolant.color,
                          "Range color not saved and loaded from prefs file")

        self.assertEquals(rpm_range.min,
                          new_rpm.min,
                          "Range min not saved and loaded from prefs file")
        self.assertEquals(rpm_range.max,
                          new_rpm.max,
                          "Range max not saved and loaded from prefs file")
        self.assertEquals(rpm_range.color,
                          new_rpm.color,
                          "Range color not saved and loaded from prefs file")

    #Not running this test as Kivy's Clock.create_trigger doesn't execute
    #outside of the Kivy env
    def save_timer(self):
        prefs = UserPrefs(self.data_dir, save_timeout=1)
        rpm_range = Range(1000, 8000)
        prefs.set_range_alert('RPM', rpm_range)

        time.sleep(3)

        new_prefs = UserPrefs(self.data_dir, save_timeout=1000)
        new_rpm_range = new_prefs.get_range_alert('RPM')

        self.assertEquals(rpm_range.min, new_rpm_range.min, "UserPrefs not saved automatically")
