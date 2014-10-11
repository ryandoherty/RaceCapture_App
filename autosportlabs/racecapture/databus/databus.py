from autosportlabs.racecapture.data.sampledata import SampleData

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
	
	def update(self, channel, value):
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
	self.rcApi = None
	self.databus = None
	self.sample = SampleData()
	
	def __init__(self, databus, rcApi, **kwargs):
		super(DataBusPump, self).__init__(**kwargs)
		self.rcApi = rcApi
		self.databus = databus
		sampleThread = Thread(target=self.sampleWorker)
		sampleThread.daemon = True
		sampleThread.start()
		
		
	def on_sample(self, sampleData):
		pass
		
	def sampleWorker(self):
		databus = self.databus
		rcApi = self.rcApi
		rcApi.addListener(self, 's', self.on_sample)
		pass
		
		
	
