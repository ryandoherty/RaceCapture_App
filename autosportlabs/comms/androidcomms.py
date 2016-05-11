import traceback
import threading
import Queue
from time import sleep
from jnius import autoclass
import jnius
from kivy.logger import Logger

BTConn = autoclass('com.autosportlabs.racecapture.BluetoothConnection')

PORT_OPEN_DELAY = 5
SERVICE_START_DELAY = 5

class PortNotOpenException(Exception):
    pass

class CommsErrorException(Exception):
    pass

class AndroidComms(object):
    CONNECT_TIMEOUT = 10.0
    DEFAULT_TIMEOUT = 1.0
    device = None
    _timeout = DEFAULT_TIMEOUT
    _oscid = None
    _reader_thread = None

    def __init__(self, device):
        self.device = device
        _reader_should_run = None
        _reader_thread = None
        self._bt_conn = BTConn.createInstance();
        self.supports_streaming = True

    def get_available_devices(self):
        bt_devices = self._bt_conn.getAvailableDevices()
        Logger.info('AndroidComms: detected ports: {}'.format(','.join(bt_devices)))
        return bt_devices

    def isOpen(self):
        return self._bt_conn.isOpen()

    def open(self):
        Logger.info('AndroidComms: Opening connection ' + str(self.device))
        self._bt_conn.open(self.device)
        Logger.info('AndroidComms: after open')

    def keep_alive(self):
        pass

    def close(self):
        Logger.info('AndroidComms: close')
        self._bt_conn.close()

    def read_message(self):
        return self._bt_conn.readLine()

    def write_message(self, message):
        if not self._bt_conn.write(message):
            raise CommsErrorException()
