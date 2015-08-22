from kivy.logger import Logger
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.event import EventDispatcher
import threading
import asynchat, asyncore
import json
import socket
import sys
import errno
import math

class TelemetryManager(EventDispatcher):
    RETRY_WAIT = 2
    channels = ObjectProperty(None)
    device_id = StringProperty(None)

    def __init__(self, data_bus, device_id=None, host=None, port=None, **kwargs):
        super(TelemetryManager, self).__init__(**kwargs)

        self.host = 'race-capture.com'
        self.port = 8080
        self.connection = None
        self.auto_start = False
        self._connection_process = None

        self.register_event_type('on_connected')
        self.register_event_type('on_disconnected')
        self.register_event_type('on_streaming')
        self.register_event_type('on_config_updated')
        self.register_event_type('on_error')

        self._data_bus = data_bus
        self.device_id = device_id

        self._data_bus.addMetaListener(self._on_meta)
        self._data_bus.start_update()

        meta = self._data_bus.getMeta()

        if len(meta) > 1:
            self.channels = meta
        else:
            self.channels = None

        if host is not None:
            self.host = host

        if port is not None:
            self.port = port

        if 'auto_start' in kwargs:
            self.auto_start = kwargs.get('auto_start')

        if self.auto_start:
            self.start()

    def _on_meta(self, channel_metas):
        Logger.info("TelemetryManager: Got meta")
        self.channels = channel_metas

    def on_channels(self, instance, value):
        Logger.info("TelemetryManager: Got channels")
        if not self._connection_process and self.auto_start:
            self.start()

    def on_device_id(self, instance, value):
        # Disconnect, re-auth, etc
        Logger.info("TelemetryManager: Got new device id")

        if not self._connection_process and self.auto_start:
            self.start()
        elif self._connection_process:
            Logger.info("TelemetryManager: connection previously established, restarting")
            self.connection.end()  # Connection will re-start

    def on_config_updated(self, config):
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    def on_config_written(self, config):
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    def start(self):
        Logger.info("TelemetryManager: start()")
        if self._connection_process:
            # We have a connection object, could be alive or dead
            if self._connection_process.is_alive():
                pass
            else:
                self._connect()
        else:
            if self.device_id and self.channels:
                Logger.info("TelemetryManager: starting telemetry thread")
                self._connect()
            else:
                Logger.warning('TelemetryManager: Device id and/or channels missing '
                               'when attempting to start, waiting for config to get device id')
                self.auto_start = True

    def _connect(self):
        Logger.info("TelemetryManager: starting connection")
        self.connection = TelemetryConnection(self.host, self.port, self.device_id,
                                              self.channels, self._data_bus, self.status)
        self._connection_process = threading.Thread(target=self.connection.run)
        self._connection_process.daemon = True
        self._connection_process.start()
        Logger.info("TelemetryManager: thread started")

    def stop(self):
        Logger.info("TelemetryManager: stop()")
        self.connection.end()

    def status(self, status, msg, status_code):
        if status_code == TelemetryConnection.STATUS_CONNECTED:
            self.dispatch('on_connected', msg)
        elif status_code == TelemetryConnection.STATUS_DISCONNECTED:
            self.dispatch('on_disconnected', msg)
            threading.Timer(self.RETRY_WAIT, self._connect).start()
        elif status_code == TelemetryConnection.STATUS_STREAMING:
            self.dispatch('on_streaming', msg)
        elif status_code in [TelemetryConnection.ERROR_AUTHENTICATING,
                             TelemetryConnection.ERROR_CONNECTING,
                             TelemetryConnection.ERROR_UNKNOWN,
                             TelemetryConnection.ERROR_UNKNOWN_MESSAGE]:
            self.dispatch('on_error', msg)

    def on_connected(self, *args):
        pass

    def on_streaming(self, *args):
        pass

    def on_disconnected(self, *args):
        pass

    def on_error(self, *args):
        pass


class TelemetryConnection(asynchat.async_chat):

    STATUS_UNINITIALIZED = -1
    STATUS_DISCONNECTED = 0
    STATUS_CONNECTED = 1
    STATUS_AUTHORIZED = 2
    STATUS_STREAMING = 3

    ERROR_CONNECTING = 0
    ERROR_AUTHENTICATING = 1
    ERROR_UNKNOWN = 2
    ERROR_CONNECTION_REFUSED = 3
    ERROR_TIMEOUT = 4
    ERROR_UNKNOWN_MESSAGE = 5

    def __init__(self, host, port, device_id, channels, data_bus, update_status_cb, timeout=5):
        asynchat.async_chat.__init__(self)

        self.status = self.STATUS_UNINITIALIZED
        self.input_buffer = []
        self.timeout = timeout
        self._connect_timeout_timer = None
        self._sample_timer = None

        # State is hard
        self.connected = False
        self._connecting = False
        self.authorized = False
        self.streaming = False
        self.meta_sent = False

        self._channel_data = channels
        self._sample_data = None
        self._error = False

        self.host = host
        self.port = port
        self.device_id = device_id
        self._data_bus = data_bus
        self._update_status = update_status_cb

        self._data_bus.add_sample_listener(self._on_sample)
        self._data_bus.addMetaListener(self._on_meta)
        self.set_terminator("\n")

    def _on_sample(self, sample):
        self._sample_data = sample

    def _on_meta(self, meta):
        Logger.info("TelemetryConnection: got new meta")
        if self.authorized:
            self._channel_data = meta

            if self._sample_timer:
                self._sample_timer.cancel()

            self._send_meta()
            self._start_sample_timer()

    def _start_sample_timer(self):
        self._sample_timer = threading.Timer(0.1, self._send_sample)
        self._sample_timer.start()

    def run(self):
        Logger.info("TelemetryConnection: connecting to: " + self.host + " " + str(self.port))

        self._connecting = True

        # No try/except here because the connect call ends up calling socket.connect_ex,
        # which does not throw any errors. Async FTW! (Sorta)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))

        asyncore.loop()

    def close_connection(self):
        self.close_when_done()

    def handle_connect(self):
        Logger.info("TelemetryConnection: got connect")

    def handle_expt(self):
        # Something really bad happened if we're here
        Logger.info("TelemetryConnection: handle_expt, closing connection")
        self._update_status("ok", "Unknown error, disconnected from RaceCapture/Live", self.STATUS_DISCONNECTED)
        self.close_when_done()

    def handle_write(self):
        Logger.info("TelemetryConnection: socket writable")
        self._update_status("ok", "Connected to RaceCapture/Live", self.STATUS_CONNECTED)
        self.connected = True
        self._connecting = False
        self._send_auth()

    def handle_close(self):
        self.connected = False
        self._connecting = False
        Logger.info("TelemetryConnection: got disconnect")
        self._update_status("ok", "Disconnected from RaceCapture/Live", self.STATUS_DISCONNECTED)

    def handle_accept(self):
        Logger.info("TelemetryConnection: handle_accept()")

    def handle_error(self):
        # Guess what, when async_chat has errors, it calls this with 0 information
        # So we have to inspect the callstack to figure out what happened. \o/
        t, v, trace = sys.exc_info()

        # Socket error objects will have a .errno attribute
        if hasattr(v, 'errno'):
            if v.errno == errno.ECONNREFUSED:
                Logger.info("TelemetryConnection: connection refused")
                self._update_status("error", "Connection refused", self.ERROR_CONNECTION_REFUSED)
            elif v.errno == errno.ETIMEDOUT:
                Logger.info("TelemetryConnection: timeout connecting")
                self._update_status("error", "Timeout connecting", self.ERROR_TIMEOUT)
            else:
                Logger.info("TelemetryConnection: unknown error connecting " + str(t) + " " +str(v))
                self._update_status("error", "Timeout connecting", self.ERROR_UNKNOWN)
        else:
            Logger.info("TelemetryConnection: unknown error " + str(v))
            self._update_status("error", "Unknown error connecting", self.ERROR_UNKNOWN)

        self.connected = False
        self._connecting = False
        self.streaming = False
        self.authorized = False
        self._error = True
        self.close_when_done()

    def send_msg(self, msg):
        msg = msg + "\n"
        msg = msg.encode('ascii')

        self.push(msg)

    def collect_incoming_data(self, data):
        self.input_buffer.append(data)

    def found_terminator(self):
        msg = ''.join(self.input_buffer)
        self.input_buffer = []

        Logger.info("TelemetryConnection: " + msg)
        msg_object = json.loads(msg)
        self._handle_msg(msg_object)

    def _handle_msg(self, msg_object):
        if "status" in msg_object:
            if msg_object["status"] == "ok" and not self.authorized:
                self._update_status("ok", "Authorized with RaceCapture/Live",
                                    self.STATUS_AUTHORIZED)
                Logger.info("TelemetryConnection: authorized to RaceCapture/Live")
                self.authorized = True
                self._send_meta()
                self._start_sample_timer()
            elif not self.authorized:
                # We failed, abort
                Logger.info("TelemetryConnection: failed to authorize, closing")
                self._update_status("error", "Failed to authorize with RaceCapture/Live",
                                    self.ERROR_AUTHENTICATING)
                self.close_connection()
        else:
            Logger.error("TelemetryConnection: unknown message. Msg: " + str(msg_object))
            self._update_status("error", "Unknown telemetry message", self.ERROR_UNKNOWN_MESSAGE)

    def _send_auth(self):
        Logger.info("TelemetryConnection: sending auth")
        auth_cmd = '{"cmd":{"schemaVer":2,"auth":{"deviceId":"' + self.device_id + '"}}}'
        self.send_msg(auth_cmd)

    def _send_meta(self):
        # Meta format: {"s":{"meta":[{"nm":"Coolant","ut":"F","sr":1},{"nm":"MAP","ut":"KPa","sr":5}]}}
        Logger.info("TelemetryConnection: sending meta")

        msg = {"s":{"meta":[]}}
        meta = []

        for channel_name, channel_config in self._channel_data.iteritems():
            channel = {
                "nm": channel_config.name,
                "ut": channel_config.units,
                "sr": channel_config.sampleRate,
                "min": channel_config.min,
                "max": channel_config.max
            }
            meta.append(channel)

        msg["s"]["meta"] = meta
        msg_json = json.dumps(msg)

        self.send_msg(msg_json)

    def _send_sample(self):
        if self._sample_data is not None:
            update = {"s": {"d": None}}
            bitmasks = []
            bitmasks_needed = int(max(0, math.floor((len(self._channel_data) - 1) / 32)) + 1)
            channel_bit_position = 0
            bitmask_index = 0

            data = []

            for x in range(0, bitmasks_needed):
                bitmasks.append(0)

            for channel_name, value in self._channel_data.iteritems():
                if channel_bit_position > 31:
                    bitmask_index += 1
                    channel_bit_position = 0

                if channel_name in self._sample_data:
                    value = self._sample_data[channel_name]
                    bitmasks[bitmask_index] = bitmasks[bitmask_index] | (1 << channel_bit_position)
                    data.append(value)

                channel_bit_position += 1

            for bitmask in bitmasks:
                data.append(bitmask)

            update["s"]["d"] = data
            update_json = json.dumps(update)

            self.send_msg(update_json)
            self._start_sample_timer()

    def end(self):
        Logger.info("TelemetryConnection: end()")
        if self.connected:
            self._sample_timer.cancel()
            self.close_when_done()

