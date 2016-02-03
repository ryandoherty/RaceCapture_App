import unittest
import json
from autosportlabs.racecapture.config.rcpconfig import VersionConfig


class SampleDataTest(unittest.TestCase):

    def test_version_info(self):
        version_config = VersionConfig()

        self.assertFalse(version_config.is_valid)

        version_config.name = 'RCP_MK2'
        version_config.major = '3'
        version_config.serial = '123456'

        self.assertTrue(version_config.is_valid)

def main():
    unittest.main()

if __name__ == "__main__":
    main()
