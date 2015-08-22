#!/usr/bin/python
import unittest
#from kivy.logger import Logger
#Logger.setLevel(51) #Hide all Kivy Logger calls

loader = unittest.TestLoader()
tests = loader.discover('.')
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
