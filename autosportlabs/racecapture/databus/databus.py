from kivy.clock import Clock
from time import sleep
from kivy.logger import Logger
from threading import Thread, Event
from autosportlabs.racecapture.data.channels import ChannelMeta
from autosportlabs.racecapture.data.sampledata import Sample, SampleMetaException, ChannelMetaCollection
from autosportlabs.racecapture.databus.filter.bestlapfilter import BestLapFilter
from autosportlabs.racecapture.databus.filter.laptimedeltafilter import LaptimeDeltaFilter
from autosportlabs.util.threadutil import safe_thread_exit, ThreadSafeDict
from utils import is_mobile_platform

DEFAULT_DATABUS_UPDATE_INTERVAL = 0.02  # 50Hz UI update rate

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
    channel_metas = ThreadSafeDict()
    channel_data = ThreadSafeDict()
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

    def start_update(self, interval=DEFAULT_DATABUS_UPDATE_INTERVAL):
        if self._polling:
            return

        Clock.schedule_interval(self.notify_listeners, interval)
        self._polling = True

    def stop_update(self):
        Clock.unschedule(self.notify_listeners)
        self._polling = False

    def _update_datafilter_meta(self, datafilter):
        channel_metas = self.channel_metas
        metas = datafilter.get_channel_meta(channel_metas)
        with self.channel_metas as cm:
            for channel, meta in metas.iteritems():
                cm[channel] = meta

    def update_channel_meta(self, metas):
        """update channel metadata information
        This should be called when the channel information has changed
        """
        # update channel metadata
        with self.channel_metas as cm, self.channel_data as cd:
            # clear our list of channel data values, in case channels
            # were removed on this metadata update
            cd.clear()

            # clear and reload our channel metas
            cm.clear()
            for meta in metas.channel_metas:
                cm[meta.name] = meta

            # add channel meta for existing filters
            for f in self.data_filters:
                self._update_datafilter_meta(f)

        self.meta_updated = True
        self.rcp_meta_read = True

    def addSampleListener(self, callback):
        self.sample_listeners.append(callback)

    def update_samples(self, sample):
        """Update channel data with new samples
        """
        with self.channel_data as cd:
            for sample_item in sample.samples:
                channel = sample_item.channelMeta.name
                value = sample_item.value
                cd[channel] = value

            # apply filters to updated data
            for f in self.data_filters:
                f.filter(cd)

    def notify_listeners(self, dt):

        if self.meta_updated:
            with self.channel_metas as cm:
                self.notify_meta_listeners(cm)
                self.meta_updated = False

        with self.channel_data as cd:
            for channel, value in cd.iteritems():
                self.notify_channel_listeners(channel, value)

            for listener in self.sample_listeners:
                listener(cd)

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

    def remove_sample_listener(self, listener):
        '''
        Remove the specified sample listener
        :param listener
        :type object / callback function
        '''
        Logger.info('DataBus: remove sample listener {}'.format(listener))
        try:
            self.sample_listeners.remove(listener)
        except Exception as e:
            Logger.error('Could not remove sample listener {}: {}'.format(listener, e))
        
    def remove_meta_listener(self, listener):
        '''
        Remove the specified meta listener
        :param listener
        :type object / callback function
        '''
        Logger.info('DataBus: remove meta listener {}'.format(listener))
        try:
            self.meta_listeners.remove(listener)
        except Exception as e:
            Logger.error('Could not remove meta listener {}: {}'.format(listener, e))
        
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

SAMPLE_POLL_TEST_TIMEOUT = 3.0
SAMPLE_POLL_INTERVAL_TIMEOUT = 0.02  # 50Hz polling
SAMPLE_POLL_EVENT_TIMEOUT = 1.0
SAMPLE_POLL_EXCEPTION_RECOVERY = 10.0
SAMPLES_TO_WAIT_FOR_META = 5.0

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

    def start(self, data_bus, rc_api):
        if self._running.is_set():
            # since we're already running, simply
            # request updated metadata
            self.meta_is_stale()
            return
                    
        self._rc_api = rc_api
        self._data_bus = data_bus
        rc_api.addListener('s', self.on_sample)
        rc_api.addListener('meta', self.on_meta)
        self._running.set()
        if not is_mobile_platform():
            #only start the worker on desktop mode
            t = Thread(target=self.sample_worker)
            t.start()
            self._sample_thread = t

    def stop(self):
        self._running.clear()
        try:
            if self._sample_thread is not None:
                self._sample_thread.join()
        except Exception as e:
            Logger.warning('DataBusPump: Failed to join sample_worker: {}'.format(e))

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
            if sample.updated_meta:
                dataBus.update_channel_meta(sample.metas)
            dataBus.update_samples(sample)
            self._sample_event.set()
        except SampleMetaException:
            # this is to prevent repeated sample meta requests
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
        Logger.info('DataBusPump: sample_worker starting')
        while self._running.is_set():
            try:
                rc_api.sample()
                sleep(SAMPLE_POLL_INTERVAL_TIMEOUT)
            except Exception as e:
                Logger.error('DataBusPump: Exception in sample_worker: ' + str(e))
                sleep(SAMPLE_POLL_EXCEPTION_RECOVERY)

        Logger.info('DataBusPump: sample_worker exiting')
        safe_thread_exit()

