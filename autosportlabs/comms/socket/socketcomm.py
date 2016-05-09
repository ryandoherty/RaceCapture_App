from kivy.logger import Logger

KEEP_ALIVE_TIMEOUT_S = 4
COMMAND_CLOSE = 'CLOSE'
COMMAND_KEEP_ALIVE = 'PING'

class SocketComm():
    CONNECT_TIMEOUT = 1.0
    DEFAULT_TIMEOUT = 1.0
    QUEUE_FULL_TIMEOUT = 1.0
    _timeout = DEFAULT_TIMEOUT
    port = None
    _connection = None
    _connection_process = None
    _rx_queue = None
    _tx_queue = None
    _command_queue = None

    def __init__(self, **kwargs):
        self.port = kwargs.get('port')
        self._connection = kwargs.get('connection')
        Logger.info('SocketComm: init')

    def start_connection_process(self):
        pass

    def get_available_ports(self):
        return []

    def isOpen(self):
        pass

    def open(self):
        pass

    def keep_alive(self):
        pass

    def close(self):
        pass

    def read_message(self):
        pass

    def write_message(self, message):
        pass
