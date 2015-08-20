from kivy.logger import Logger
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.event import EventDispatcher
import threading
import asynchat, socket, asyncore
import json
import socket
import sys
import errno


class TelemetryManager(EventDispatcher):
    MAX_RETRIES = 5
    channels = ObjectProperty(None)
    device_id = StringProperty(None)

    def __init__(self, data_bus, device_id=None, host=None, port=None, **kwargs):
        super(TelemetryManager, self).__init__(**kwargs)

        self.host = 'race-capture.com'
        self.port = 8080
        self.connection = None
        self.auto_start = True
        self._connection_process = None
        self._retry_count = 0

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

        if len(meta) > 0:
            self.channels = meta

        if host is not None:
            self.host = host

        if port is not None:
            self.port = port

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
                self.connection = TelemetryConnection(self.host, self.port, self.device_id,
                                                      self.channels, self._data_bus, self.status)
                self._connection_process = threading.Thread(target=self.connection.run)
                self._connection_process.daemon = True
                self._connection_process.start()
                Logger.info("TelemetryManager: thread started")
                self._connection_timer = threading.Timer(5.0, self._check_connection)
                self._connection_timer.start()
            else:
                Logger.warning("TelemetryManager: Device id and/or channels missing when attempting to start, waiting for config to get device id")
                self.auto_start = True

    def stop(self):
        Logger.info("TelemetryManager: stop()")
        self._connection_timer.cancel()
        self.connection.end()

    def _check_connection(self):
        if self._connection_process.is_alive():
            Logger.info("TelemetryManager: thread is alive")
        else:
            Logger.info("TelemetryManager: thread is dead")
        self._connection_timer = threading.Timer(5.0, self._check_connection)
        self._connection_timer.start()

    def status(self, status, msg, status_code):
        if status_code == TelemetryConnection.STATUS_CONNECTED:
            self.dispatch('on_connected', msg)
        elif status_code == TelemetryConnection.STATUS_DISCONNECTED:
            self.dispatch('on_disconnected', msg)
        elif status_code == TelemetryConnection.STATUS_STREAMING:
            self.dispatch('on_streaming', msg)
        elif status_code in [TelemetryConnection.ERROR_AUTHENTICATING,
                             TelemetryConnection.ERROR_CONNECTING,
                             TelemetryConnection.ERROR_UNKNOWN]:
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

    def __init__(self, host, port, device_id, meta, data_bus, update_status_cb, timeout=5):
        asynchat.async_chat.__init__(self)

        self.status = self.STATUS_UNINITIALIZED
        self.input_buffer = []
        self.timeout = timeout
        self._connect_timeout_timer = None

        #State is hard
        self._connected = False
        self._connecting = False
        self._authorized = False
        self.meta_sent = False

        self._channel_data = {}
        self._update_status = None
        self._error = False

        self.host = host
        self.port = port
        self.device_id = device_id
        self.meta = meta
        self._data_bus = data_bus
        self._update_status = update_status_cb

        self._data_bus.add_sample_listener(self._on_sample)
        self._data_bus.addMetaListener(self._on_meta)
        self.set_terminator("\n")

    def _on_sample(self, sample):
        self._channel_data = sample

    def _on_meta(self, meta):
        # TODO: stop sending data to RCL, send meta, start sending data
        self.meta = meta

    def run(self):
        # TODO: handle timeouts due to network
        Logger.info("TelemetryConnection: connecting to: " + self.host + " " + str(self.port))

        self._connecting = True

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))

        asyncore.loop()

    def close_connection(self):
        self.close_when_done()

    def handle_connect(self):
        Logger.info("TelemetryConnection: got connect")

    def handle_expt(self):
        #Something really bad happened if we're here
        Logger.info("TelemetryConnection: handle_expt, closing connection")
        self.close()

    def handle_write(self):
        Logger.info("TelemetryConnection: socket writable")
        self._update_status("ok", "Connected to RaceCapture/Live", self.STATUS_CONNECTED)
        self._connected = True
        self._connecting = False
        self._send_auth()

    def handle_close(self):
        self._connected = False
        self._connecting = False
        Logger.info("TelemetryConnection: got disconnect")
        self._update_status("ok", "Disconnected from RaceCapture/Live", self.STATUS_DISCONNECTED)
        self.close()

    def handle_accept(self):
        Logger.info("TelemetryConnection: handle_accept()")

    def handle_error(self):
        #Guess what, when async_chat has errors, it calls this with 0 information
        #So we have to inspect the callstack to figure out what happened. \o/
        t, v, trace = sys.exc_info()

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
            Logger.info("TelemetryConnection: unknown error")
            self._update_status("error", "Timeout connecting", self.ERROR_UNKNOWN)

        self._error = True
        self.close()

    def send_msg(self, msg):
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
            if msg_object["status"] == "ok" and not self._authorized:
                self._update_status("ok", "Authorized with RaceCapture/Live",
                                    self.STATUS_AUTHORIZED)
                Logger.info("TelemetryConnection: authorized to RaceCapture/Live")
                self._authorized = True
                self._send_meta()
            elif not self._authorized:
                # We failed, abort
                Logger.info("TelemetryConnection: failed to authorize, closing")
                self._update_status("error", "Failed to authorize with RaceCapture/Live",
                                    self.ERROR_AUTHENTICATING)
                self.close_connection()
        else:
            Logger.error("TelemetryConnection: unknown error. Msg: " + str(msg_object))
            self._update_status("error", "Unknown telemetry error", self.ERROR_UNKNOWN)

    def _send_auth(self):
        Logger.info("TelemetryConnection: sending auth")
        auth_cmd = '{"cmd":{"schemaVer":2,"auth":{"deviceId":"' + self.device_id + '"}}}' + "\n"
        self.send_msg(auth_cmd)

    def _send_meta(self):
        #{"s":{"meta":[{"nm":"Coolant","ut":"F","sr":1},{"nm":"MAP","ut":"KPa","sr":5}]}}
        pass

    def end(self):
        Logger.info("TelemetryConnection: end()")
        if self._connected:
            self.close_when_done()

