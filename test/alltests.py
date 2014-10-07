import glob
import unittest
from test.racecapture.databus.test_databus import DataBusTest

def create_test_suite():
    test_file_strings = glob.glob('test/racecapture/databus/test_*.py')
    print(test_file_strings)
    module_strings = ['test.'+str[5:len(str)-3] for str in test_file_strings]
    suites = [unittest.defaultTestLoader.loadTestsFromName(name) \
              for name in module_strings]
    testSuite = unittest.TestSuite(suites)
    return testSuite