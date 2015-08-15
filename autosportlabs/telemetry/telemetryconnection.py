from kivy.logger import Logger
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.event import EventDispatcher
import threading
import asynchat, socket


class TelemetryManager(EventDispatcher):
    host = 'race-capture.com'
    port = 8080
    connect_timeout = 5
    channels = ObjectProperty(None)
    streaming_data = False
    device_id = StringProperty(None)
    socket = None
    connection = None
    auto_start = True
    _connection_process = None
    _data_bus = None
    _transmitting = False
    _connection_output = None
    _connection_input = None

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
        Logger.info("TelemetryManager: got channels")
        if not self._connection_process and self.auto_start:
            self.start()
        elif self._connection_process:
            #New meta, need to pause, send new channel info and restart
            Logger.info("TelemetryManager: connection exists, stopping and starting")
            self.stop()
            self.start()

    def on_device_id(self, instance, value):
        # Disconnect, re-auth, etc
        Logger.info("TelemetryManager: Got new device id")

        if not self._connection_process and self.auto_start:
            self.start()
        elif self._connection_process:
            Logger.info("TelemetryManager: connection previously established, restarting")

    def on_config_updated(self, config):
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    def on_config_written(self, config):
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    def start(self):
        Logger.info("TelemetryManager: start()")
        if not self._connection_process:
            if self.device_id and self.channels:
                Logger.info("TelemetryManager: starting telemetry thread")
                self._connection_input, self._connection_output = Pipe()
                self.connection = TelemetryConnection(self.host, self.port, self.device_id, self.channels)
                self._connection_process = threading.Thread(target=self.connection.run, args=(self._connection_output, self._connection_input))
                self._connection_process.start()
            else:
                Logger.warning("TelemetryManager: Device id and/or channels missing when attempting to start, waiting for config to get device id")

    def stop(self):
        Logger.info("TelemetryManager: stop()")

class TelemetryConnection(asynchat.async_chat):

    host = None
    port = None
    device_id = None
    timeout = None
    meta = None
    _output_pipe = None
    _input_pipe = None

    def __init__(self, host, port, device_id, meta, timeout=5):
        asyncore.dispatcher.__init__(self)
        self.host = host
        self.port = port
        self.device_id = device_id
        self.meta = meta
        self.timeout = timeout

    def run(self, output_pipe, input_pipe):
        self._output_pipe = output_pipe
        self._input_pipe = input_pipe

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(self.host, self.port)
        Logger.info("TelemetryConnection: thread started")

    def handle_read(self):
        pass

    def handle_write(self):
        pass

