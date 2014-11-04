import time
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

SAMPLE_POLL_WAIT_TIMEOUT       = 0.2 #5Hz polling
SAMPLE_POLL_EXCEPTION_RECOVERY = 2.0

class DataBusPump(object):
    _rc_api = None
    _data_bus = None
    sample = Sample()
    _sample_event = Event()
    _running = Event()
    _sample_thread = None
    
    def __init__(self, **kwargs):
        super(DataBusPump, self).__init__(**kwargs)

    def startDataPump(self, data_bus, rc_api):
        self._rc_api = rc_api
        self._data_bus = data_bus
        self._running.set()
        self._sample_thread = Thread(target=self.sample_worker)
        self._sample_thread.daemon = True
        self._sample_thread.start()

    def on_meta(self, meta_json):
        metas = self.sample.metas
        metas.fromJson(meta_json.get('meta'))
        self._data_bus.updateMeta(metas)
    
    def on_sample(self, sample_json):
        sample = self.sample
        dataBus = self._data_bus
        try:
            sample.fromJson(sample_json)
            dataBus.updateSample(sample)
            if sample.updated_meta:
                dataBus.updateMeta(sample.metas)
                self._sample_event.set()
        except SampleMetaException as e:
            print('SampleMeta Exception: {}'.format(str(e)))
            self.request_meta()

    def stopDataPump(self):
        self._running.clear()
        self._sample_thread.join()

    def request_meta(self):
        self._rc_api.get_meta()
    
    def sample_worker(self):
        rc_api = self._rc_api
        sample_event = self._sample_event
        rc_api.addListener('s', self.on_sample)
        rc_api.addListener('meta', self.on_meta)
        request_meta = True
        
        print("DataBus Sampler Starting")
        sample_event.set()
        while self._running.is_set():
            try:
                if sample_event.wait(SAMPLE_POLL_WAIT_TIMEOUT) != True:
                    rc_api.sample(request_meta)
                    if request_meta == True:
                        if len(self.sample.metas.channel_metas) > 0:
                            request_meta = False
            except Exception as e:
                time.sleep(SAMPLE_POLL_EXCEPTION_RECOVERY)
                print('Exception in sample_worker: ' + str(e))
            finally:
                sample_event.clear()
                
        print("DataBus Sampler Exiting")

