class DataBus(object):
	channelData = {}
	channelListeners = {}
	
	def __init__(self, **kwargs):
		super(DataBus, self).__init__(**kwargs)
	
	def update(self, channel, value):
		self.channelData[channel] = value
		self.notifyListeners(channel, value)
	
	def notifyListeners(self, channel, value):
		listeners = self.channelListeners.get(channel)
		if not listeners == None:
			for listener in listeners:
				listener(value)
				
	def getData(self, channel):
		return self.channelData[channel]
	
	def addListener(self, channel, callback):
		listeners = self.channelListeners.get(channel)
		if listeners == None:
			listeners = [callback]
			self.channelListeners[channel] = listeners
		else:
			listeners.append(callback)
		
