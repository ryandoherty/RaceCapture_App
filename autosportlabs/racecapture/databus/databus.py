import time
from threading import Thread
from autosportlabs.racecapture.data.sampledata import Sample

class DataBus(object):
	channelData = {}
	sampleListeners = []
	channelListeners = {}
	metaListeners = []
	channelMetas = None
	
	def __init__(self, **kwargs):
		super(DataBus, self).__init__(**kwargs)
	
	def updateMeta(self, channelMetas):
		self.channelMetas = channelMetas
		self.notifyMetaListeners(channelMetas)
	
	def getMeta(self):
		return self.channelMetas
	
	def updateSample(self, sample):
		for sampleItem in sample.samples:
			channel = sampleItem.channelMeta.name
			value = sampleItem.value
			self.channelData[channel] = value
			self.notifyChannelListeners(channel, value)
			
		self.notifySampleListeners(sample)
	
	def getData(self, channel):
		return self.channelData[channel]

	def notifySampleListeners(self, sample):
		for listener in self.sampleListeners:
			listener(sample)
			
	def notifyChannelListeners(self, channel, value):
		listeners = self.channelListeners.get(channel)
		if not listeners == None:
			for listener in listeners:
				listener(value)
				
	def notifyMetaListeners(self, channelMeta):
		for listener in self.metaListeners:
			listener(channelMeta)			
	
	def addSampleListener(self, callback):
		self.sampleListeners.append(callback)
			
	def addChannelListener(self, channel, callback):
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
		dataBus.updateSample(sample)
		if sample.updatedMeta:
			dataBus.updateMeta(sample.channelMetas)
			
	def sampleWorker(self):
		rcApi = self.rcApi
		dataBus = self.dataBus
		rcApi.addListener('s', self.on_sample)
		while True:
			try:
				rcApi.sample(self.dataBus.channelMetas == None)
				time.sleep(.1)
			except:
				time.sleep(2)
				pass
		
		
	
