from kivy.logger import Logger
import threading
import Queue
from Queue import Empty
from time import sleep
import traceback
from autosportlabs.comms.commscommon import PortNotOpenException

KEEP_ALIVE_TIMEOUT_S = 4
COMMAND_CLOSE = 'CLOSE'
COMMAND_KEEP_ALIVE = 'PING'


def connection_thread_message_reader(rx_queue, connection, should_run):
    Logger.debug('SocketComm: connection thread message reader started')

    while should_run.is_set():
        try:
            msg = connection.read(should_run)
            if msg:
                rx_queue.put(msg)
        except:
            Logger.error('SocketComm: Exception in connection_process_message_reader')
            Logger.debug(traceback.format_exc())
            should_run.clear()
            sleep(0.5)
    Logger.debug('SocketComm: connection process message reader exited')


def connection_thread_message_writer(tx_queue, connection, should_run):
    Logger.info('SocketComm: connection thread message writer started')
    while should_run.is_set():
        try:
            message = tx_queue.get(True, 1.0)
            if message:
                Logger.info("SocketComm: writing message {}".format(message))
                connection.write(message)
        except Empty:
            pass
        except Exception as e:
            Logger.error('SocketComm: Exception in connection_thread_message_writer ' + str(e))
            Logger.debug(traceback.format_exc())
            should_run.clear()
            sleep(0.5)
    Logger.debug('SocketComm: connection thread message writer exited')


def connection_message_thread(connection, address, rx_queue, tx_queue, command_queue):
    Logger.info('SocketComm: connection process starting')

    try:
        connection.open(address)
        connection.flushInput()
        connection.flushOutput()

        reader_writer_should_run = threading.Event()
        reader_writer_should_run.set()

        reader_thread = threading.Thread(target=connection_thread_message_reader, args=(rx_queue, connection,
                                                                                        reader_writer_should_run))
        reader_thread.start()

        writer_thread = threading.Thread(target=connection_thread_message_writer, args=(tx_queue, connection,
                                                                                        reader_writer_should_run))
        writer_thread.start()

        while reader_writer_should_run.is_set():
            try:
                command = command_queue.get(True, STAY_ALIVE_TIMEOUT)
                if command == COMMAND_CLOSE:
                    Logger.debug('SocketComm: connection thread: got close command')
                    reader_writer_should_run.clear()
            except Empty:
                Logger.debug('SocketComm: keep alive timeout')
                reader_writer_should_run.clear()
        Logger.debug('SocketComm: connection worker exiting')

        reader_thread.join()
        writer_thread.join()

        try:
            connection.close()
        except:
            Logger.error('SocketComm: Exception closing connection worker connection')
            Logger.error(traceback.format_exc())
    except Exception as e:
        Logger.error('SocketComm: Exception setting up connection thread: ' + str(type(e)) + str(e))
        Logger.debug(traceback.format_exc())

    Logger.debug('SocketComm: connection worker exited')


class SocketComm():
    CONNECT_TIMEOUT = 1.0
    DEFAULT_TIMEOUT = 1.0
    QUEUE_FULL_TIMEOUT = 1.0
    _timeout = DEFAULT_TIMEOUT
    _connection_process = None
    _rx_queue = None
    _tx_queue = None
    _command_queue = None

    def __init__(self, connection, device):
        self.device = device
        self._connection = connection
        Logger.info('SocketComm: init')

    def start_connection_process(self):
        rx_queue = Queue.Queue()
        tx_queue = Queue.Queue(5)
        command_queue = Queue.Queue()
        connection_thread = threading.Thread(target=connection_message_thread, args=(self._connection, self.device,
                                                                                     rx_queue, tx_queue, command_queue))
        connection_thread.start()
        self._rx_queue = rx_queue
        self._tx_queue = tx_queue
        self._command_queue = command_queue
        self._connection_process = connection_thread

    def get_available_devices(self):
        return self._connection.get_available_devices()

    def isOpen(self):
        return self._connection_process is not None and self._connection_process.is_alive()

    def open(self):
        if not self.isOpen():
            self.start_connection_process()

    def keep_alive(self):
        try:
            self._command_queue.put_nowait(COMMAND_KEEP_ALIVE)
        except:
            pass

    def close(self):
        Logger.debug('SocketComm: close()')
        if self.isOpen():
            try:
                Logger.debug('SocketComm: closing connection process')
                self._command_queue.put_nowait(COMMAND_CLOSE)
                self._connection_process.join(self._timeout * 2)
                Logger.debug('SocketComm: connection process joined')
            except:
                Logger.debug('SocketComm: Timeout joining connection process')

    def read_message(self):
        if not self.isOpen():
            raise PortNotOpenException('Port Closed')
        try:
            return self._rx_queue.get(True, self._timeout)
        except:  # returns Empty object if timeout is hit
            return None

    def write_message(self, message):
        if not self.isOpen(): raise PortNotOpenException('Port Closed')
        self._tx_queue.put(message, True, SocketComm.QUEUE_FULL_TIMEOUT)

