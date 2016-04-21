from kivy.logger import Logger
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.event import EventDispatcher
from kivy.clock import Clock
from time import sleep
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
    channels = ObjectProperty(None, allownone=True)
    device_id = StringProperty(None)
    cell_enabled = BooleanProperty(False)
    telemetry_enabled = BooleanProperty(False)

    def __init__(self, data_bus, device_id=None, host=None, port=None, **kwargs):
        self.host = 'telemetry.podium.live'
        self.port = 8080
        self.connection = None
        self._connection_process = None
        self._retry_timer = None
        self._retry_wait = self.RETRY_WAIT_START
        self._retry_count = 0
        self._auth_failed = False

        self.register_event_type('on_connecting')
        self.register_event_type('on_connected')
        self.register_event_type('on_disconnected')
        self.register_event_type('on_streaming')
        self.register_event_type('on_config_updated')
        self.register_event_type('on_config_written')
        self.register_event_type('on_error')
        self.register_event_type('on_auth_error')

        self._data_bus = data_bus
        self.device_id = device_id

        # We do this here because we need to have some of our class initialized
        super(TelemetryManager, self).__init__(**kwargs)

        self._data_bus.addMetaListener(self._on_meta)
        self._data_bus.start_update()

        if host is not None:
            self.host = host

        if port is not None:
            self.port = port

        if self._data_bus.rcp_meta_read:
            self.channels = self._data_bus.getMeta()

        if 'telemetry_enabled' in kwargs:
            self.telemetry_enabled = kwargs.get('telemetry_enabled')

    # Event handler for when meta (channel list) changes
    def _on_meta(self, channel_metas):
        Logger.debug("TelemetryManager: Got meta")
        self.channels = channel_metas

    # Event handler for when self.channels changes, don't restart connection b/c
    # the TelemetryConnection object will handle new channels
    def on_channels(self, instance, value):
        Logger.debug("TelemetryManager: Got channels")

        if self.telemetry_enabled:
            self.start()

    # Event handler for when self.device_id changes, need to restart connection
    def on_device_id(self, instance, value):
        # Disconnect, re-auth, etc
        Logger.info("TelemetryManager: Got new device id")

        if value == "":
            self.stop()

        if self._connection_process and self._connection_process.is_alive():
            Logger.info("TelemetryManager: connection previously established, restarting")
            self.connection.end()  # Connection will re-start
            self._connection_process.join(0.1)

        if self.telemetry_enabled:
            self.start()

    def on_cell_enabled(self, instance, value):
        Logger.debug("TelemetryManager: on_cell_enabled: " + str(value))
        if value:
            self._user_stopped()
        else:
            Logger.info("TelemetryManager: on_cell_enabled, starting")
            self.start()

    def on_telemetry_enabled(self, instance, value):
        Logger.debug("TelemetryManager: on_telemetry_enabled: " + str(value))
        if value:
            self.start()
        else:
            self._user_stopped()

    # Event handler for when config is pulled from RCP
    def on_config_updated(self, config):
        self.cell_enabled = config.connectivityConfig.cellConfig.cellEnabled
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    # Event handler for when config is written to RCP
    def on_config_written(self, config):
        self.cell_enabled = config.connectivityConfig.cellConfig.cellEnabled
        self.device_id = config.connectivityConfig.telemetryConfig.deviceId

    # Starts connection, checks to see if requirements are met
    def start(self):
        Logger.info("TelemetryManager: start() telemetry_enabled: " + str(self.telemetry_enabled) + " cell_enabled: " + str(self.cell_enabled))
        self._auth_failed = False

        if self.telemetry_enabled and not self.cell_enabled and self.device_id != "" and self.channels is not None:
            if self._connection_process and not self._connection_process.is_alive():
                Logger.info("TelemetryManager: connection process is dead")
                self._connect()
            elif not self._connection_process:
                if self.device_id and self.channels:
                    Logger.debug("TelemetryManager: starting telemetry thread")
                    self._connect()
                else:
                    Logger.warning('TelemetryManager: Device id, channels missing or RCP cell enabled '
                                   'when attempting to start. Aborting.')

    # Creates new TelemetryConnection in separate thread
    def _connect(self):
        Logger.info("TelemetryManager: starting connection")
        self.dispatch('on_connecting', "Connecting to Podium")
        self.connection = TelemetryConnection(self.host, self.port, self.device_id,
                                              self.channels, self._data_bus, self.status)
        self._connection_process = threading.Thread(target=self.connection.run)
        self._connection_process.daemon = True
        self._connection_process.start()
        Logger.debug("TelemetryManager: thread started")

    def stop(self):
        Logger.debug("TelemetryManager: stop()")

        if self._retry_timer:
            self._retry_timer.cancel()

        if self.connection:
            self.connection.end()
            try:
                self._connection_process.join(1)
            except:
                pass

    def _user_stopped(self):
        self.dispatch('on_disconnected', '')
        self.channels = None
        self.stop()

    # Status function that receives events from TelemetryConnection thread
    # Bubbles up events into main app
    def status(self, status, msg, status_code):
        Logger.debug("TelemetryManager: got telemetry status: " + str(status) + " message: " + str(msg) + " code: " + str(status_code))
        if status_code == TelemetryConnection.STATUS_CONNECTED:
            self.dispatch('on_connected', msg)
        elif status_code == TelemetryConnection.STATUS_AUTHORIZED:
            self._retry_count = 0
        elif status_code == TelemetryConnection.ERROR_AUTHENTICATING:
            Logger.warning("TelemetryManager: authentication failed")
            self._auth_failed = True
            self.stop()
            self.dispatch('on_auth_error', "Podium: invalid device id")
        elif status_code == TelemetryConnection.STATUS_DISCONNECTED:
            Logger.info("TelemetryManager: disconnected")
            self.stop()
            if not self._auth_failed:
                self.dispatch('on_disconnected', msg)

            if self.telemetry_enabled and not self.cell_enabled and not self._auth_failed:
                wait = self.RETRY_WAIT_START if self._retry_count == 0 else \
                    min(self.RETRY_WAIT_MAX_TIME, (math.pow(self.RETRY_MULTIPLIER, self._retry_count) *
                                                   self.RETRY_WAIT_START))
                Logger.warning("TelemetryManager: got disconnect, reconnecting in %d seconds" % wait)
                self._retry_timer = threading.Timer(wait, self._connect)
                self._retry_timer.start()
                self._retry_count += 1
        elif status_code == TelemetryConnection.STATUS_STREAMING:
            self.dispatch('on_streaming', True)
        elif status_code in [TelemetryConnection.ERROR_CONNECTING,
                             TelemetryConnection.ERROR_UNKNOWN,
                             TelemetryConnection.ERROR_UNKNOWN_MESSAGE]:
            self.dispatch('on_error', msg)

    def on_connecting(self, *args):
        pass

    def on_connected(self, *args):
        pass

    def on_streaming(self, *args):
        pass

    def on_disconnected(self, *args):
        pass

    def on_error(self, *args):
        pass

    def on_auth_error(self, *args):
        pass

# Handles connecting to RCL, auth, sending data
class TelemetryConnection(asynchat.async_chat):

    STATUS_UNINITIALIZED = -1
    STATUS_DISCONNECTED = 0
    STATUS_CONNECTED = 1
    STATUS_AUTHORIZED = 2
    STATUS_STREAMING = 3

    ERROR_UNKNOWN_MESSAGE = -10
    ERROR_CONNECTING = 10
    ERROR_AUTHENTICATING = 11
    ERROR_UNKNOWN = 12
    ERROR_CONNECTION_REFUSED = 13
    ERROR_TIMEOUT = 14

    SAMPLE_INTERVAL = 0.1

    def __init__(self, host, port, device_id, channel_metas, data_bus, update_status_cb):
        asynchat.async_chat.__init__(self)

        self.status = self.STATUS_UNINITIALIZED
        self.input_buffer = []
        self._connect_timeout_timer = None
        self._sample_timer = None
        self._running = threading.Event()

        # State is hard
        self._connected = False
        self._connecting = False
        self.authorized = False
        self.meta_sent = False

        self._channel_metas = channel_metas
        self._sample_data = None

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
        Logger.info("TelemetryConnection: got new meta")
        if self.authorized:
            try:
                self._channel_metas = meta
                self._send_meta()
            except Exception as e:
                Logger.warn("TelemetryConnection: Failed to send meta: {}".format(e))

    # Sets up timer to send data to RCL every 100ms
    def _start_sample_timer(self):
        self._running.set()
        self._sample_timer = threading.Thread(target=self._sample_worker)
        self._sample_timer.daemon = True
        self._sample_timer.start()

    def _sample_worker(self):
        Logger.info('TelemetryConnection: sample worker starting')
        while self._running.is_set():
            try:
                self._send_sample()
                sleep(self.SAMPLE_INTERVAL)
            except Exception as e:
                Logger.error("TelemetryConnection: error sending sample: " + str(e))
        Logger.info('TelemetryConnection: sample worker exiting')

    def run(self):
        Logger.info("TelemetryConnection: connecting to: %s:%d" % (self.host, self.port))

        self._connecting = True

        # No try/except here because the connect call ends up calling socket.connect_ex,
        # which does not throw any errors. Async FTW! (Sorta)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.connect((self.host, self.port))
        except:
            Logger.info("TelemetryConnection: exception connecting")
            self._update_status("error", "Podium: Error connecting", self.STATUS_DISCONNECTED)

        # This starts the loop around the socket connection polling
        # 'timeout' is how long the select() or poll() functions will wait for data,
        # set to 3 seconds as the default is 30s, which means our code wouldn't
        # see a disconnect until 30s after it happens
        asyncore.loop(timeout=3)

    def handle_connect(self):
        Logger.info("TelemetryConnection: got connect")
        if not self._connected:
            self._update_status("ok", "Podium connected", self.STATUS_CONNECTED)
            self._connected = True
            self._connecting = False
            self._send_auth()

    def handle_expt(self):
        # Something really bad happened if we're here
        Logger.error("TelemetryConnection: handle_expt, closing connection")
        self._update_status("error", "Podium: unknown error", self.STATUS_DISCONNECTED)
        self.end()

    def handle_close(self):
        self.close()
        self._connected = False
        self._connecting = False
        self.authorized = False
        Logger.info("TelemetryConnection: got disconnect")
        self._update_status("ok", "Podium disconnected", self.STATUS_DISCONNECTED)

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
        if not trace:  # Must have a traceback
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
                Logger.error("TelemetryConnection: unknown error connecting " + str(t) + " " + str(v))
                self._update_status("error", "Unknown error", self.ERROR_UNKNOWN)
            self.end()
        else:
            if v.__class__.__name__ == 'IndexError':  # asynchat is not thread-safe and throws this error randomly
                return
            Logger.error("TelemetryConnection: unknown error " + str(v) + str(file) + " " + str(function) + ":" + str(line))
            self._update_status("error", "Unknown error ", self.ERROR_UNKNOWN)

    def send_msg(self, msg):
        msg = msg + "\n"
        msg = msg.encode('ascii')

        try:
            self.push(msg)
        except Exception as e:
            Logger.error("TelemetryConnection: error sending message: " + str(e))

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
                self._update_status("ok", "Podium authorized",
                                    self.STATUS_AUTHORIZED)
                Logger.info("TelemetryConnection: authorized to Podium")
                self.authorized = True
                self._send_meta()
                self._start_sample_timer()
                self._update_status("ok", False,
                                    self.STATUS_STREAMING)
            elif not self.authorized:
                # We failed, abort
                Logger.info("TelemetryConnection: failed to authorize, closing")
                self._update_status("error", "Podium: Auth failed",
                                    self.ERROR_AUTHENTICATING)
                self.end()
        else:
            Logger.error("TelemetryConnection: unknown message. Msg: " + str(msg_object))
            self._update_status("error", "Unknown telemetry message", self.ERROR_UNKNOWN_MESSAGE)

        if "message" in msg_object:
            Logger.debug("TelemetryConnection: got message: " + msg_object["message"])

    def _send_auth(self):
        Logger.debug("TelemetryConnection: sending auth")
        auth_cmd = '{"cmd":{"schemaVer":2,"auth":{"deviceId":"' + self.device_id + '"}}}'
        self.send_msg(auth_cmd)

    def _send_meta(self):
        # Meta format: {"s":{"meta":[{"nm":"Coolant","ut":"F","sr":1},{"nm":"MAP","ut":"KPa","sr":5}]}}
        Logger.info("TelemetryConnection: sending meta")

        msg = {"s":{"meta":[]}}
        meta = []

        with self._channel_metas as cm:
            for channel_config in cm.itervalues():
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

    def _send_sample(self, *args):
        if self._sample_data is not None:
            update = {"s": {"d": None}}
            bitmasks = []
            channel_bit_position = 0
            bitmask_index = 0
            data = []
            with self._sample_data as sd, self._channel_metas as cm:
                bitmasks_needed = int(max(0, math.floor((len(cm) - 1) / 32)) + 1)
                for x in range(0, bitmasks_needed):
                    bitmasks.append(0)

                for channel_name, value in cm.iteritems():
                    if channel_bit_position > 31:
                        bitmask_index += 1
                        channel_bit_position = 0

                    value = sd.get(channel_name)
                    if value is not None:
                        bitmasks[bitmask_index] = bitmasks[bitmask_index] | (1 << channel_bit_position)
                        data.append(value)

                    channel_bit_position += 1

            for bitmask in bitmasks:
                data.append(bitmask)

            update["s"]["d"] = data
            update_json = json.dumps(update)

            self.send_msg(update_json)

    def end(self):
        self._data_bus.remove_meta_listener(self._on_meta)
        self._data_bus.remove_sample_listener(self._on_sample)
        if self._connected:
            self._running.clear()
            Logger.info("TelemetryConnection: closing connection")
            if self._sample_timer:
                self._sample_timer.join()
            self.close_when_done()

