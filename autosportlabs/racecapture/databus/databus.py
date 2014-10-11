import time
from threading import Thread
from autosportlabs.racecapture.data.sampledata import Sample

class DataBus(object):
	channelData = {}
	channelListeners = {}
	metaListeners = []
	channelMeta = None
	
	def __init__(self, **kwargs):
		super(DataBus, self).__init__(**kwargs)
	
	def updateMeta(self, channelMeta):
		self.channelMeta = channelMeta
		self.notifyMetaListeners(channelMeta)
	
	def getMeta(self):
		return self.channelMeta
	
	def updateData(self, channel, value):
		self.channelData[channel] = value
		self.notifyListeners(channel, value)
	
	def getData(self, channel):
		return self.channelData[channel]

	def notifyListeners(self, channel, value):
		listeners = self.channelListeners.get(channel)
		if not listeners == None:
			for listener in listeners:
				listener(value)
				
	def notifyMetaListeners(self, channelMeta):
		for listener in self.metaListeners:
			listener(channelMeta)			
	
	def addListener(self, channel, callback):
		listeners = self.channelListeners.get(channel)
		if listeners == None:
			listeners = [callback]
			self.channelListeners[channel] = listeners
		else:
			listeners.append(callback)
	
	def addMetaListener(self, callback):
		self.metaListeners.append(callback)
		
class DataBusPump(object):
	rcApi = None
	dataBus = None
	sample = Sample()
	
	def __init__(self, **kwargs):
		super(DataBusPump, self).__init__(**kwargs)
		
	def startDataPump(self, dataBus, rcApi):
		self.rcApi = rcApi
		self.dataBus = dataBus
		sampleThread = Thread(target=self.sampleWorker)
		sampleThread.daemon = True
		sampleThread.start()
		
	def on_sample(self, sampleJson):
		sample = self.sample
		dataBus = self.dataBus
		sample.fromJson(sampleJson)
		for sampleItem in sample.samples:
			print('sample ' + str(sampleItem.value) + ' ' + str(sampleItem.channelConfig.name))
			dataBus.updateData(sampleItem.value, sampleItem.channelConfig.name)
			
	def sampleWorker(self):
		rcApi = self.rcApi
		dataBus = self.dataBus
		rcApi.addListener('s', self.on_sample)
		while True:
			rcApi.sample(self.dataBus.channelMeta == None)
			time.sleep(1)
		
		
	
