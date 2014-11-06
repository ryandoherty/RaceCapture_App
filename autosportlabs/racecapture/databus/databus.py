from time import sleep
from threading import Thread, Event
from autosportlabs.racecapture.data.sampledata import Sample, ChannelMeta, SampleMetaException,\
    ChannelMetaCollection
from kivy.clock import Clock

class DataBus(object):
    channelData = {}
    sampleListeners = []
    channelListeners = {}
    metaListeners = []
    channel_metas = {}

    def __init__(self, **kwargs):
        super(DataBus, self).__init__(**kwargs)

    def updateMeta(self, metas, async = True):
        print('updating databus meta')
        self.channel_metas.clear()
        for meta in metas.channel_metas:
            self.channel_metas[meta.name] = meta
        if async: 
            Clock.schedule_once(lambda dt: self.notifyMetaListeners(self.channel_metas))
        else:
            self.notifyMetaListeners(self.channel_metas)

    def getMeta(self):
        return self.channel_metas

    def updateSample(self, sample, async = True):
        for sampleItem in sample.samples:
            channel = sampleItem.channelMeta.name
            value = sampleItem.value            
            self.channelData[channel] = value
        if async:
            Clock.schedule_once(lambda dt: self.notifySampleListeners(sample))
        else:
            self.notifySampleListeners(sample)
    
    def getData(self, channel):
        return self.channelData[channel]

    def notifySampleListeners(self, sample):

        for sampleItem in sample.samples:
            channel = sampleItem.channelMeta.name
            value = sampleItem.value
            self.notifyChannelListeners(channel, value)
        
        for listener in self.sampleListeners:
                listener(sample)

    def notifyChannelListeners(self, channel, value):
        listeners = self.channelListeners.get(str(channel))
        if listeners:
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


    def removeChannelListener(self, channel, callback):
        try:
            listeners = self.channelListeners.get(channel)
            if listeners:
                listeners.remove(callback)
        except:
            pass
            
                    
    def addMetaListener(self, callback):
        self.metaListeners.append(callback)

SAMPLE_POLL_TEST_TIMEOUT       = 2.0
SAMPLE_POLL_INTERVAL_TIMEOUT   = 0.1 #10Hz polling
SAMPLE_POLL_EXCEPTION_RECOVERY = 2.0
SAMPLES_TO_WAIT_FOR_META       = 10

class DataBusPump(object):
    _rc_api = None
    _data_bus = None
    sample = Sample()
    _sample_event = Event()
    _running = Event()
    _sample_thread = None
    _meta_is_stale_counter = 0
    
    def __init__(self, **kwargs):
        super(DataBusPump, self).__init__(**kwargs)

    def startDataPump(self, data_bus, rc_api):
        self._rc_api = rc_api
        self._data_bus = data_bus

        rc_api.addListener('s', self.on_sample)
        rc_api.addListener('meta', self.on_meta)
        
        self._running.set()
        self._sample_thread = Thread(target=self.sample_worker)
        self._sample_thread.daemon = True
        self._sample_thread.start()

    def on_meta(self, meta_json):
        metas = self.sample.metas
        metas.fromJson(meta_json.get('meta'))
        self._data_bus.updateMeta(metas)
        self._meta_is_stale_counter = 0
    
    def on_sample(self, sample_json):
        sample = self.sample
        dataBus = self._data_bus
        try:
            sample.fromJson(sample_json)
            dataBus.updateSample(sample)
            if sample.updated_meta:
                dataBus.updateMeta(sample.metas)
            self._sample_event.set()
        except SampleMetaException:
            #this is to prevent repeated sample meta requests
            self._request_meta_handler()

    def _request_meta_handler(self):
            if self._meta_is_stale_counter <= 0:
                print('Sample Meta is stale, requesting meta')
                self._meta_is_stale_counter = SAMPLES_TO_WAIT_FOR_META
                self.request_meta()
            else:
                self._meta_is_stale_counter -= 1
        
    def stopDataPump(self):
        self._running.clear()
        self._sample_thread.join()

    def request_meta(self):
        self._rc_api.get_meta()
    
    def sample_worker(self):
        rc_api = self._rc_api
        sample_event = self._sample_event
        
        print("DataBus Sampler Starting")
        sample_event.clear()
        if sample_event.wait(SAMPLE_POLL_TEST_TIMEOUT) == True:
            print('Async sampling detected')
        else:
            print("Synchronous sampling mode enabled")
            while self._running.is_set():
                try:
                    #the timeout here is designed to be longer than the streaming rate of 
                    #RaceCapture. If we don't get an asynchronous sample, then we will timeout
                    #and request a sample anyway.
                    rc_api.sample()
                    sample_event.wait(SAMPLE_POLL_INTERVAL_TIMEOUT)
                    sample_event.clear()
                    sleep(SAMPLE_POLL_INTERVAL_TIMEOUT)
                except Exception as e:
                    time.sleep(SAMPLE_POLL_EXCEPTION_RECOVERY)
                    print('Exception in sample_worker: ' + str(e))
                finally:
                    sample_event.clear()
                
        print("DataBus Sampler Exiting")

