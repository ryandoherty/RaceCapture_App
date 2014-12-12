import traceback
import threading
import Queue
from time import sleep
from kivy.lib import osc
from android import AndroidService

CMD_API                 = '/rc_cmd'
TX_API                  = '/rc_tx'
RX_API                  = '/rc_rx'

SERVICE_API_PORT        = 3000
CLIENT_API_PORT         = 3001

SERVICE_CMD_EXIT        = 'EXIT'
SERVICE_CMD_OPEN        = 'OPEN'
SERVICE_CMD_CLOSE       = 'CLOSE'
SERVICE_CMD_KEEP_ALIVE  = 'PING'
SERVICE_CMD_GET_PORTS   = 'GET_PORTS'

SERVICE_STARTUP_DELAY   = 5
class PortNotOpenException(Exception):
    pass

class CommsErrorException(Exception):
    pass


def message_reader(rx_queue, oscid, should_run):
    print('connection process message reader started')
    
    while should_run.is_set():
        try:
            osc.readQueue(oscid)
            sleep(0.1)
        except:
            print('Exception in message_reader')
            traceback.print_exc()
            #_rx_queue.put('##ERROR##')
            sleep(0.5)
    print('connection process message reader exited')            
    
class AndroidComms(object):
    CONNECT_TIMEOUT = 10.0
    DEFAULT_TIMEOUT = 1.0
    port = None
    _timeout = DEFAULT_TIMEOUT
    _rx_queue = None
    _oscid = None
    _reader_thread = None
    _service = None
    
    def __init__(self, **kwargs):
        self.port = kwargs.get('port')
        _reader_should_run = None
        _reader_thread = None
        self._rx_queue = Queue.Queue()
        osc.init()
        oscid = osc.listen(ipAddr='0.0.0.0', port=CLIENT_API_PORT)
        osc.bind(oscid, self.on_rx, RX_API)
        osc.bind(oscid, self.on_command, CMD_API)
        self._oscid = oscid
        
        service = AndroidService('RC comms service', 'running')
        service.start('service started')
        self._service = service

    def on_command(self, message, *args):
        message = message[2]
        if message == 'ERROR':
            print('Error on connection')
            self.close()
        
    def on_rx(self, message, *args):
        message = message[2]
        self._rx_queue.put(message)
                
    def start_connection_process(self):
        reader_should_run = threading.Event()
        reader_should_run.set()
    
        reader_thread = threading.Thread(target=message_reader, args=(self._rx_queue, self._oscid, reader_should_run))
        self._reader_should_run = reader_should_run
        self._reader_thread = reader_thread
        reader_thread.start()
        sleep(SERVICE_STARTUP_DELAY)
        self.send_service_command(SERVICE_CMD_OPEN)
                                
    def get_available_ports(self):
        return ['RaceCapturePro'] #TODO get this from the service directly
    
    def isOpen(self):
        return self._reader_thread != None and self._reader_thread.is_alive()
    
    def open(self):
        print('Opening connection ' + str(self.port))
        self.start_connection_process()
    
    def keep_alive(self):
        self.send_service_command(SERVICE_CMD_KEEP_ALIVE)
    
    def close(self):
        print('comms.close()')
        if self.isOpen():
            self.send_service_command(SERVICE_CMD_CLOSE)
            try:
                print('closing reader_thread')
                self._reader_should_run.clear()
                self._reader_thread.join(self._timeout)
                print('reader_thread joined')
            except:
                print('Timeout joining reader_thread')

    def read_message(self):
        try:
            return self._rx_queue.get(True, self._timeout)
        except: #returns Empty object if timeout is hit
            return None
    
    def write_message(self, message):
        self.send_service_tx_message(message)

    def send_service_command(self, cmd):
        osc.sendMsg(CMD_API, [cmd,], port=SERVICE_API_PORT)
        
    def send_service_tx_message(self, message):
        osc.sendMsg(TX_API, [message,], port=SERVICE_API_PORT)
                    