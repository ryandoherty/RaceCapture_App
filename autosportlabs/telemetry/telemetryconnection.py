from kivy.logger import Logger
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.event import EventDispatcher
from multiprocessing import Process
import asyncore


class TelemetryManager(EventDispatcher):
    host = 'race-capture.com'
    port = 8080
    connect_timeout = 5
    channels = ObjectProperty(None)
    streaming_data = False
    device_id = StringProperty(None)
    socket = None
    connection = None
    auto_start = False
    _data_bus = None
    _transmitting = False

    def __init__(self, data_bus, device_id=None, **kwargs):
        super(TelemetryManager, self).__init__(**kwargs)

        self.register_event_type('on_config_updated')
        self.register_event_type('on_config_written')

        self._data_bus = data_bus
        self.device_id = device_id

        self._data_bus.addMetaListener(self._on_meta)
        self._data_bus.start_update()

        if 'host' in kwargs:
            self.host = kwargs.get('host')

        if 'port' in kwargs:
            self.port = kwargs.get('port')

        if 'auto_start' in kwargs:
            self.auto_start = kwargs.get('auto_start')

        if self.auto_start:
            self.start()

    def _on_meta(self, channel_metas):
        self.channels = channel_metas

    def on_channels(self, instance, value):
        # If we are connected, need to stop sending telemetry and send new meta
        # Also we need to send meta when we connect
        if self._transmitting:
            self.stop()
            self._send_meta()
            self.start()

    def on_device_id(self):
        # Disconnect, re-auth, etc
        pass

    def on_config_updated(self, config):
        self.device_id = config.connectivityConfig.deviceId

    def on_config_written(self, config):
        self.device_id = config.connectivityConfig.deviceId

    def start(self):
        if not self.connection_process:
            if self.device_id and self.channels:
                self.connection = TelemetryConnection(self.host, self.port, self.device_id, self.channels)
                self.connection_process = Process(target=self.connection.run)
                self.connection_process.start()
            else:
                Logger.warning("TelemetryManager: Device id and/or channels missing when attempting to start, waiting for config to get device id")

    def stop(self):
        pass

class TelemetryConnection(asyncore.dispatcher):

    host = None
    port = None
    device_id = None
    timeout = None
    meta = None

    def __init__(self, host, port, device_id, meta, timeout=5):
        asyncore.dispatcher.__init__(self)
        self.host = host
        self.port = port
        self.device_id = device_id
        self.meta = meta
        self.timeout = timeout

    def run(self):
        Logger.info("TelemetryConnection: thread started")

