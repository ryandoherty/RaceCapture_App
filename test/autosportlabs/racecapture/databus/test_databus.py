import unittest
from autosportlabs.racecapture.databus.databus import DataBus

class DataBusTest(unittest.TestCase):
	def test_write_value(self):
		dataBus = DataBus()
		dataBus.update('testChannel', 123.456)

def main():
	unittest.main()

if __name__ == "__main__":
	main()