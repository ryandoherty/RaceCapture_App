import time
from threading import Thread, Event
from autosportlabs.racecapture.data.sampledata import Sample, SampleMetaException

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
		
SAMPLE_POLL_WAIT_TIMEOUT 		= 4.0
SAMPLE_POLL_INTERVAL	 		= 0.1
SAMPLE_POLL_EXCEPTION_RECOVERY 	= 2.0

class DataBusPump(object):
	rcApi = None
	dataBus = None
	sample = Sample()
	sampleEvent = None
	shouldGetMeta = True
	
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
		try:
			sample.fromJson(sampleJson)
			dataBus.updateSample(sample)
			if sample.updatedMeta:
				dataBus.updateMeta(sample.channelMetas)
				self.shouldGetMeta = False			
		except SampleMetaException as e:
			print('SampleMeta Exception: {}'.format(str(e)))
			self.shouldGetMeta = True
		finally:
			self.sampleEvent.set()
			
	def sampleWorker(self):
		rcApi = self.rcApi
		dataBus = self.dataBus
		sampleEvent = Event()
		self.sampleEvent = sampleEvent
		sampleEvent.set()
		rcApi.addListener('s', self.on_sample)
		while True:
			try:
				sampleEvent.wait(SAMPLE_POLL_WAIT_TIMEOUT)
				rcApi.sample(self.shouldGetMeta)
				time.sleep(SAMPLE_POLL_INTERVAL)
			except:
				time.sleep(SAMPLE_POLL_EXCEPTION_RECOVERY)
				self.shouldGetMeta = True
				pass
		
		
	
