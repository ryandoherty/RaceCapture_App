import unittest
from autosportlabs.racecapture.databus.databus import DataBus

class DataBusTest(unittest.TestCase):
	def test_update_value(self):
		dataBus = DataBus()
		dataBus.updateData('RPM', 1234)
		
		value = dataBus.getData('RPM')
		self.assertEqual(value, 1234)

	listenerVal0 = None
	def test_listener(self):
		
		def listener(value):
			self.listenerVal0 = value

		dataBus = DataBus()
		dataBus.addListener('RPM', listener)
		dataBus.updateData('RPM', 1111)
		self.assertEqual(self.listenerVal0, 1111)
	
	listenerVal1 = None
	listenerVal2 = None
	def test_multiple_listeners(self):
		def listener1(value):
			self.listenerVal1 = value

		def listener2(value):
			self.listenerVal2 = value
			
		dataBus = DataBus()
		dataBus.addListener('RPM', listener1)
		dataBus.addListener('RPM', listener2)
		dataBus.updateData('RPM', 1111)
		self.assertEqual(self.listenerVal1, 1111)
		self.assertEqual(self.listenerVal2, 1111)
		
	listenerVal3 = None
	listenerVal4 = None
	def test_mixed_listeners(self):
		def listener3(value):
			self.listenerVal3 = value

		def listener4(value):
			self.listenerVal4 = value
			
		dataBus = DataBus()
		dataBus.addListener('RPM', listener3)
		dataBus.addListener('EngineTemp', listener4)
		dataBus.updateData('RPM', 1111)
		#ensure we don't set the wrong listener
		self.assertEqual(self.listenerVal3, 1111)
		self.assertEqual(self.listenerVal4, None)
		
		dataBus.updateData('EngineTemp', 199)
		#ensure we don't affect unrelated channels
		self.assertEqual(self.listenerVal3, 1111)
		self.assertEqual(self.listenerVal4, 199)
		
	def test_no_listener(self):
		dataBus = DataBus()
		dataBus.updateData('EngineTemp', 200)
		#no listener for this channel, should not cause an error
	
	channelMeta = None
	def test_meta_listener(self):
		dataBus = DataBus()
		
		def metaListener(channel):
			self.channelMeta = channel

		meta = object()
		dataBus.addMetaListener(metaListener)
		dataBus.updateMeta(meta)
		self.assertEqual(self.channelMeta, meta)
		
def main():
	unittest.main()

if __name__ == "__main__":
	main()