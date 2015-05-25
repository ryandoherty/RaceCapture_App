import traceback
import threading
import Queue
from time import sleep
from jnius import autoclass
import jnius

BTConn = autoclass('com.autosportlabs.racecapture.BluetoothConnection')

PORT_OPEN_DELAY   = 5
SERVICE_START_DELAY = 5

class PortNotOpenException(Exception):
    pass

class CommsErrorException(Exception):
    pass
    
class AndroidComms(object):
    CONNECT_TIMEOUT = 10.0
    DEFAULT_TIMEOUT = 1.0
    port = None
    _timeout = DEFAULT_TIMEOUT
    _oscid = None
    _reader_thread = None
    
    def __init__(self, **kwargs):
        self.port = kwargs.get('port')
        _reader_should_run = None
        _reader_thread = None
        print("AndroidComms loading")
        self._bt_conn = BTConn.createInstance();
        print("AndroidComms loading done")
                                                                
    def get_available_ports(self):
        return ['RaceCapturePro'] #TODO get this from the service directly
    
    def isOpen(self):
        return self._bt_conn.isOpen()
    
    def open(self):
        print('Opening connection ' + str(self.port))
        self._bt_conn.open(self.port)
        print('after open!!!!!!!!!!!!!!!!')
    
    def keep_alive(self):
        pass
    
    def cleanup(self):
        print('comms.cleanup()')
        
    def close(self):
        print('comms.close()')
        self._bt_conn.close()

    def read_message(self):
        return self._bt_conn.readLine()
    
    def write_message(self, message):
        if not self._bt_conn.write(message):
            raise CommsErrorException()
                    