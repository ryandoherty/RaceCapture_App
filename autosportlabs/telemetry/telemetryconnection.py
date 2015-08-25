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

"""Manager that creates a new telemetry connection in a separate thread
  Bubbles up connection events back up to the main app, watch for disconnects
  and attempts to reconnect.

  Requires channels and device id before connecting.

 Init => start() => telemetry thread => bubble up events
"""
class TelemetryManager(EventDispatcher):
    RETRY_WAIT_START = 0.1
    RETRY_MULTIPLIER = 10
    RETRY_WAIT_MAX_TIME = 10
    channels = ObjectProperty(None)
    device_id = StringProperty(None)

    def __init__(self, data_bus, device_id=None, host=None, port=None, **kwargs):
        super(TelemetryManager, self).__init__(**kwargs)

        self.host = 'race-capture.com'
        self.port = 8080
        self.connection = None
        self.auto_start = False
        self._connection_process = None
        self._retry_timer = None
        self._retry_wait = self.RETRY_WAIT_START
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

        if host is not None:
            self.host = host

        if port is not None:
            self.port = port

        if 'auto_start' in kwargs:
            self.auto_start = kwargs.get('auto_start')

        if self._data_bus.rcp_meta_read:
            self.channels = self._data_bus.getMeta()

        if self.auto_start:
            self.start()

    # Event handler for when meta (channel list) changes
    def _on_meta(self, channel_metas):
        Logger.debug("TelemetryManager: Got meta")
        self.channels = channel_metas

    # Event handler for when self.channels changes, don't restart connection b/c
    # the TelemetryConnection object will handle new channels
    def on_channels(self, instance, value):
        Logger.debug("TelemetryManager: Got channels")
        if not self._connection_process and self.auto_start:
            self.start()

    # Event handler for when self.device_id changes, need to restart connection
    def on_device_id(self, instance, value):
        # Disconnect, re-auth, etc
        Logger.debug("TelemetryManager: Got new device id")

        if not self._connection_process and self.auto_start:
            self.start()
        elif self._connection_process:
            Logger.debug("TelemetryManager: connection previously established, restarting")
            self.connection.end()  # Connection will re-start

    # Event handler for when config is pulled from RCP
    def on_config_updated(self, config):
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    # Event handler for when config is written to RCP
    def on_config_written(self, config):
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    # Starts connection, checks to see if requirements are met
    def start(self):
        Logger.debug("TelemetryManager: start()")
        self.auto_start = True
        if self._connection_process and not self._connection_process.is_alive():
            self._connect()
        else:
            if self.device_id and self.channels:
                Logger.debug("TelemetryManager: starting telemetry thread")
                self._connect()
            else:
                Logger.warning('TelemetryManager: Device id and/or channels missing '
                               'when attempting to start, waiting for config to get device id')

    # Creates new TelemetryConnection in separate thread
    def _connect(self):
        Logger.debug("TelemetryManager: starting connection")
        self.connection = TelemetryConnection(self.host, self.port, self.device_id,
                                              self.channels, self._data_bus, self.status)
        self._connection_process = threading.Thread(target=self.connection.run)
        self._connection_process.daemon = True
        self._connection_process.start()
        Logger.debug("TelemetryManager: thread started")

    def stop(self):
        Logger.debug("TelemetryManager: stop()")
        if self.connection:
            self.connection.end()
            self.auto_start = False

        if self._retry_timer:
            self._retry_timer.cancel()

    # Status function that receives events from TelemetryConnection thread
    # Bubbles up events into main app
    def status(self, status, msg, status_code):
        if status_code == TelemetryConnection.STATUS_CONNECTED:
            self.dispatch('on_connected', msg)
            self._retry_count = 0
        elif status_code == TelemetryConnection.STATUS_DISCONNECTED:
            self.dispatch('on_disconnected', msg)
            if self.auto_start:
                wait = self.RETRY_WAIT_START if self._retry_count == 0 else \
                    min(self.RETRY_WAIT_MAX_TIME, (math.pow(self.RETRY_MULTIPLIER, self._retry_count) *
                                                   self.RETRY_WAIT_START))
                Logger.warning("TelemetryManager: got disconnect, reconnecting in 2s")
                self._retry_timer = threading.Timer(wait, self._connect)
                self._retry_timer.start()
                self._retry_count += 1
        elif status_code == TelemetryConnection.STATUS_STREAMING:
            self.dispatch('on_streaming', True)
        elif status_code in [TelemetryConnection.ERROR_AUTHENTICATING,
                             TelemetryConnection.ERROR_CONNECTING,
                             TelemetryConnection.ERROR_UNKNOWN,
                             TelemetryConnection.ERROR_UNKNOWN_MESSAGE]:
            self.dispatch('on_error', msg)

        Logger.debug("TelemetryManager: got telemetry status: " + str(status) + " message: " + str(msg))

    def on_connected(self, *args):
        pass

    def on_streaming(self, *args):
        pass

    def on_disconnected(self, *args):
        pass

    def on_error(self, *args):
        pass

# Handles connecting to RCL, auth, sending data
class TelemetryConnection(asynchat.async_chat):

    STATUS_UNINITIALIZED = -1
    STATUS_DISCONNECTED = 0
    STATUS_CONNECTED = 1
    STATUS_AUTHORIZED = 2
    STATUS_STREAMING = 3

    ERROR_UNKNOWN_MESSAGE = -1
    ERROR_CONNECTING = 0
    ERROR_AUTHENTICATING = 1
    ERROR_UNKNOWN = 2
    ERROR_CONNECTION_REFUSED = 3
    ERROR_TIMEOUT = 4

    def __init__(self, host, port, device_id, channels, data_bus, update_status_cb):
        asynchat.async_chat.__init__(self)

        self.status = self.STATUS_UNINITIALIZED
        self.input_buffer = []
        self._connect_timeout_timer = None
        self._sample_timer = None

        # State is hard
        self._connected = False
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

    # Event handler for when RCP sends data to app
    def _on_sample(self, sample):
        self._sample_data = sample

    # Event handler for when RCP's channel list changes
    def _on_meta(self, meta):
        Logger.debug("TelemetryConnection: got new meta")
        if self.authorized:
            self._channel_data = meta

            if self._sample_timer:
                self._sample_timer.cancel()

            self._send_meta()
            self._start_sample_timer()

    # Sets up timer to send data to RCL every 100ms
    def _start_sample_timer(self):
        self._sample_timer = threading.Timer(0.1, self._send_sample)
        self._sample_timer.start()

    def run(self):
        Logger.info("TelemetryConnection: connecting to: %s:%d" % (self.host, self.port))

        self._connecting = True

        # No try/except here because the connect call ends up calling socket.connect_ex,
        # which does not throw any errors. Async FTW! (Sorta)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))

        # This starts the loop around the socket connection polling
        # 'timeout' is how long the select() or poll() functions will wait for data,
        # set to 1 second as the default is 30s, which means our code wouldn't
        # see a disconnect until 30s after it happens
        asyncore.loop(timeout=1)

    def handle_connect(self):
        Logger.info("TelemetryConnection: got connect")
        if not self._connected:
            self._update_status("ok", "Connected to RaceCapture/Live", self.STATUS_CONNECTED)
            self._connected = True
            self._connecting = False
            self._send_auth()

    def handle_expt(self):
        # Something really bad happened if we're here
        Logger.error("TelemetryConnection: handle_expt, closing connection")
        self._update_status("ok", "Unknown error, disconnected from RaceCapture/Live", self.STATUS_DISCONNECTED)
        self.close_when_done()

    def handle_close(self):
        self.close()
        self._connected = False
        self._connecting = False
        self.authorized = False
        Logger.info("TelemetryConnection: got disconnect")
        self._update_status("ok", "Disconnected from RaceCapture/Live", self.STATUS_DISCONNECTED)

    # When the socket is open, not necessarily usable
    def handle_accept(self):
        Logger.debug("TelemetryConnection: handle_accept()")

    # *All* errors come here, even errors thrown in this code because all functions in this object
    # are called in the asyncore.loop() function
    def handle_error(self):
        # Guess what, when async_chat has errors, it calls this with 0 information
        # So we have to inspect the callstack to figure out what happened. \o/
        t, v, trace = sys.exc_info()

        tbinfo = []
        if not trace: # Must have a traceback
            raise AssertionError("traceback does not exist")
        while trace:
            tbinfo.append((
                trace.tb_frame.f_code.co_filename,
                trace.tb_frame.f_code.co_name,
                str(trace.tb_lineno)
            ))
            trace = trace.tb_next

        # just to be safe
        del trace

        file, function, line = tbinfo[-1]
        info = ' '.join(['[%s|%s|%s]' % x for x in tbinfo])

        # Socket error objects will have a .errno attribute
        if hasattr(v, 'errno'):
            if v.errno == errno.ECONNREFUSED:
                Logger.error("TelemetryConnection: connection refused")
                self._update_status("error", "Connection refused", self.ERROR_CONNECTION_REFUSED)
            elif v.errno == errno.ETIMEDOUT:
                Logger.error("TelemetryConnection: timeout connecting")
                self._update_status("error", "Timeout connecting", self.ERROR_TIMEOUT)
            else:
                Logger.error("TelemetryConnection: unknown error connecting " + str(t) + " " +str(v))
                self._update_status("error", "Unknown error", self.ERROR_UNKNOWN)
        else:
            Logger.error("TelemetryConnection: unknown error " + str(v) + str(file) + " " + str(function) + ":" + str(line))
            self._update_status("error", "Unknown error connecting", self.ERROR_UNKNOWN)

        self._connected = False
        self._connecting = False
        self.streaming = False
        self.authorized = False
        self._error = True
        self.close_when_done()

    def send_msg(self, msg):
        msg = msg + "\n"
        msg = msg.encode('ascii')

        self.push(msg)

    # asynchat calls this function when new data comes in, we are responsible for buffering
    def collect_incoming_data(self, data):
        self.input_buffer.append(data)

    # asynchat will find the \n for us and call this when it sees it
    def found_terminator(self):
        msg = ''.join(self.input_buffer)
        self.input_buffer = []

        Logger.debug("TelemetryConnection: " + msg)
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
                self._update_status("ok", False,
                                    self.STATUS_STREAMING)
            elif not self.authorized:
                # We failed, abort
                Logger.info("TelemetryConnection: failed to authorize, closing")
                self._update_status("error", "Failed to authorize with RaceCapture/Live",
                                    self.ERROR_AUTHENTICATING)
                self.close_when_done()
        else:
            Logger.error("TelemetryConnection: unknown message. Msg: " + str(msg_object))
            self._update_status("error", "Unknown telemetry message", self.ERROR_UNKNOWN_MESSAGE)

    def _send_auth(self):
        Logger.debug("TelemetryConnection: sending auth")
        auth_cmd = '{"cmd":{"schemaVer":2,"auth":{"deviceId":"' + self.device_id + '"}}}'
        self.send_msg(auth_cmd)

    def _send_meta(self):
        # Meta format: {"s":{"meta":[{"nm":"Coolant","ut":"F","sr":1},{"nm":"MAP","ut":"KPa","sr":5}]}}
        Logger.debug("TelemetryConnection: sending meta")

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
        Logger.debug("TelemetryConnection: end()")
        if self._connected:
            if self._sample_timer:
                self._sample_timer.cancel()
            self.close_when_done()

