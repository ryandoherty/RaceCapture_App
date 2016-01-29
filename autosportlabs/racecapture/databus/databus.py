from kivy.clock import Clock
from time import sleep
from kivy.logger import Logger
from threading import Thread, Event
from autosportlabs.racecapture.data.channels import ChannelMeta
from autosportlabs.racecapture.data.sampledata import Sample, SampleMetaException, ChannelMetaCollection
from autosportlabs.racecapture.databus.filter.bestlapfilter import BestLapFilter
from autosportlabs.racecapture.databus.filter.laptimedeltafilter import LaptimeDeltaFilter
from autosportlabs.util.threadutil import safe_thread_exit


DEFAULT_DATABUS_UPDATE_INTERVAL = 0.02 #50Hz UI update rate

class DataBusFactory(object):
    def create_standard_databus(self, system_channels):
        databus = DataBus()
        databus.add_data_filter(BestLapFilter(system_channels))
        databus.add_data_filter(LaptimeDeltaFilter(system_channels))
        return databus
    
class DataBus(object):
    """Central hub for current sample data. Receives data from DataBusPump
    Also contains the periodic updater for listeners. Updates occur in the UI thread via Clock.schedule_interval
    Architecture:    
    (DATA SOURCE) => DataBus => (LISTENERS)
    
    Typical use:
    (CHANNEL LISTENERS) => DataBus.addChannelListener()  -- listeners receive updates with a particular channel's value
    (META LISTENERS) => DataBus.addMetaListener() -- Listeners receive updates with meta data

    Note: DataBus must be started via start_update before any data flows
    """
    channel_metas = {}
    channel_data = {}
    sample = None
    channel_listeners = {}
    meta_listeners = []
    meta_updated = False
    data_filters = []
    sample_listeners = []
    _polling = False
    rcp_meta_read = False

    def __init__(self, **kwargs):
        super(DataBus, self).__init__(**kwargs)

    def start_update(self, interval = DEFAULT_DATABUS_UPDATE_INTERVAL):
        if self._polling:
            return

        Clock.schedule_interval(self.notify_listeners, interval)
        self._polling = True

    def stop_update(self):
        Clock.unschedule(self.notify_listeners)
        self._polling = False

    def _update_datafilter_meta(self, datafilter):
        metas = datafilter.get_channel_meta()
        for channel, meta in metas.iteritems():
            self.channel_metas[channel] = meta

    def update_channel_meta(self, metas):
        """update channel metadata information
        This should be called when the channel information has changed
        """
        self.channel_metas.clear()
        for meta in metas.channel_metas:
            self.channel_metas[meta.name] = meta
            
        #add channel meta for existing filters
        for f in self.data_filters:
            self._update_datafilter_meta(f)
                
        self.meta_updated = True
        self.rcp_meta_read = True

    def addSampleListener(self, callback):
        self.sample_listeners.append(callback)

    def update_samples(self, sample):
        """Update channel data with new samples
        """
        for sample_item in sample.samples:
            channel = sample_item.channelMeta.name
            value = sample_item.value
            self.channel_data[channel] = value

        #apply filters to updated data
        for f in self.data_filters:
            f.filter(self.channel_data)

    def notify_listeners(self, dt):
        sample_data = {}

        if self.meta_updated:
            self.notify_meta_listeners(self.channel_metas)
            self.meta_updated = False

        for channel,value in self.channel_data.iteritems():
            self.notify_channel_listeners(channel, value)
            sample_data[channel] = value

        for listener in self.sample_listeners:
            listener(sample_data)
                
    def notify_channel_listeners(self, channel, value):
        listeners = self.channel_listeners.get(str(channel))
        if listeners:
            for listener in listeners:
                listener(value)

    def notify_meta_listeners(self, channelMeta):
        for listener in self.meta_listeners:
            listener(channelMeta)

    def addChannelListener(self, channel, callback):
        listeners = self.channel_listeners.get(channel)
        if listeners == None:
            listeners = [callback]
            self.channel_listeners[channel] = listeners
        else:
            listeners.append(callback)

    def removeChannelListener(self, channel, callback):
        try:
            listeners = self.channel_listeners.get(channel)
            if listeners:
                listeners.remove(callback)
        except:
            pass

    def add_sample_listener(self, callback):
        self.sample_listeners.append(callback)
                    
    def addMetaListener(self, callback):
        self.meta_listeners.append(callback)

    def add_data_filter(self, datafilter):
        self.data_filters.append(datafilter)
        self._update_datafilter_meta(datafilter)
        
    def getMeta(self):
        return self.channel_metas

    def getData(self, channel):
        return self.channel_data[channel]

SAMPLE_POLL_TEST_TIMEOUT       = 3.0
SAMPLE_POLL_INTERVAL_TIMEOUT   = 0.02 #50Hz polling
SAMPLE_POLL_EVENT_TIMEOUT      = 1.0
SAMPLE_POLL_EXCEPTION_RECOVERY = 10.0
SAMPLES_TO_WAIT_FOR_META       = 5.0

class DataBusPump(object):
    """Responsible for dispatching raw JSON API messages into a format the DataBus can consume.
    Attempts to detect asynchronous messaging mode, where messages are streamed to the DataBusPump.
    If Async mode not detected, a polling thread is created to simulate this.
    """
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
        if self._sample_thread == None:
            self._rc_api = rc_api
            self._data_bus = data_bus
    
            rc_api.addListener('s', self.on_sample)
            rc_api.addListener('meta', self.on_meta)
            
            self._running.set()
            self._sample_thread = Thread(target=self.sample_worker)
            self._sample_thread.daemon = True
            self._sample_thread.start()
        else:
            #we're already running, refresh channel meta data
            self.meta_is_stale()

    def on_meta(self, meta_json):
        metas = self.sample.metas
        metas.fromJson(meta_json.get('meta'))
        self._data_bus.update_channel_meta(metas)
        self._meta_is_stale_counter = 0
    
    def on_sample(self, sample_json):
        sample = self.sample
        dataBus = self._data_bus
        try:
            sample.fromJson(sample_json)
            dataBus.update_samples(sample)
            if sample.updated_meta:
                dataBus.update_channel_meta(sample.metas)
            self._sample_event.set()
        except SampleMetaException:
            #this is to prevent repeated sample meta requests
            self._request_meta_handler()

    def _request_meta_handler(self):
            if self._meta_is_stale_counter <= 0:
                Logger.info('DataBusPump: Sample Meta is stale, requesting meta')
                self._meta_is_stale_counter = SAMPLES_TO_WAIT_FOR_META
                self.request_meta()
            else:
                self._meta_is_stale_counter -= 1
        
    def stopDataPump(self):
        self._running.clear()
        self._sample_thread.join()

    def meta_is_stale(self):
        self.request_meta()
        
    def request_meta(self):
        self._rc_api.get_meta()
    
    def sample_worker(self):
        rc_api = self._rc_api
        sample_event = self._sample_event
        
        Logger.info('DataBusPump: DataBus Sampler Starting')
        sample_event.clear()
        if sample_event.wait(SAMPLE_POLL_TEST_TIMEOUT) == True:
            Logger.info('DataBusPump: Async sampling detected')
        else:
            Logger.info('DataBusPump: Synchronous sampling mode enabled')
            while self._running.is_set():
                try:
                    #the timeout here is designed to be longer than the streaming rate of 
                    #RaceCapture. If we don't get an asynchronous sample, then we will timeout
                    #and request a sample anyway.
                    rc_api.sample()
                    sample_event.wait(SAMPLE_POLL_EVENT_TIMEOUT)
                    sample_event.clear()
                    sleep(SAMPLE_POLL_INTERVAL_TIMEOUT)
                except Exception as e:
                    sleep(SAMPLE_POLL_EXCEPTION_RECOVERY)
                    Logger.error('DataBusPump: Exception in sample_worker: ' + str(e))
                finally:
                    sample_event.clear()
                
        Logger.info('DataBusPump: DataBus Sampler Exiting')
        safe_thread_exit()

