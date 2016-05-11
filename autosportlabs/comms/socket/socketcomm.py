#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

from kivy.logger import Logger
import threading
import Queue
from Queue import Empty
from time import sleep
import traceback
from autosportlabs.comms.commscommon import PortNotOpenException


class SocketComm(object):
    """
    Responsible for communicating with a socket connection to a RC device
     Starts up threads for reading/writing data and pushes/reads data to queues
    """
    CONNECT_TIMEOUT = 1.0
    DEFAULT_TIMEOUT = 1.0
    QUEUE_FULL_TIMEOUT = 1.0
    TX_QUEUE_SIZE = 5
    KEEP_ALIVE_TIMEOUT_S = 4
    COMMAND_CLOSE = 'CLOSE'
    COMMAND_KEEP_ALIVE = 'PING'

    _timeout = DEFAULT_TIMEOUT
    _connection_process = None
    _rx_queue = None
    _tx_queue = None
    _command_queue = None

    def __init__(self, connection, device):
        """Initializes SocketComm, does not open any sockets
        :param connection The connection object to use
        :param device The IP address of the device to connect to
        :type connection SocketConnection
        :type device String
        :return None
        """
        self.device = device
        self._connection = connection
        self.supports_streaming = False
        Logger.info('SocketComm: init')

    def start_connection_process(self):
        """Starts the connection process to the device, starting up a Thread for communication over Queues
        :return None
        """
        rx_queue = Queue.Queue()
        tx_queue = Queue.Queue(self.TX_QUEUE_SIZE)
        command_queue = Queue.Queue()
        connection_thread = threading.Thread(target=self._connection_message_thread, args=(self._connection,
                                                                                           self.device, rx_queue,
                                                                                           tx_queue, command_queue))
        connection_thread.start()
        self._rx_queue = rx_queue
        self._tx_queue = tx_queue
        self._command_queue = command_queue
        self._connection_process = connection_thread

    def get_available_devices(self):
        """Returns a List of ips that a RC device was found on
        :return List of ips
        """
        return self._connection.get_available_devices()

    def isOpen(self):
        """Returns True if the RC connection is open, False if not
        :return Boolean
        """
        return self._connection_process is not None and self._connection_process.is_alive()

    def open(self):
        """Starts the connection process to the RC device
        :return None
        """
        if not self.isOpen():
            self.start_connection_process()

    def keep_alive(self):
        """Puts a command into the command queue to keep the connection alive
        :return None
        """
        try:
            self._command_queue.put_nowait(self.COMMAND_KEEP_ALIVE)
        except:
            pass

    def close(self):
        """Closes the socket connection with the RC device
        :return None
        """
        Logger.debug('SocketComm: close()')
        if self.isOpen():
            try:
                Logger.debug('SocketComm: closing connection process')
                self._command_queue.put_nowait(self.COMMAND_CLOSE)
                self._connection_process.join(self._timeout * 2)
                Logger.debug('SocketComm: connection process joined')
            except:
                Logger.debug('SocketComm: Timeout joining connection process')

    def read_message(self):
        """Reads a message from the RX queue and returns it
        :return: String or None
        """
        if not self.isOpen():
            raise PortNotOpenException('Port Closed')
        try:
            return self._rx_queue.get(True, self._timeout)
        except:  # returns Empty object if timeout is hit
            return None

    def write_message(self, message):
        """Writes a message to the TX queue, which is then written by the tx thread
        :return: None
        """
        if not self.isOpen(): raise PortNotOpenException('Port Closed')
        self._tx_queue.put(message, True, SocketComm.QUEUE_FULL_TIMEOUT)

    def _connection_thread_message_reader(self, rx_queue, connection, should_run):
        """This method is designed to be run in a thread, it will loop infinitely as long as should_run.is_set()
        returns True. In its loop it will attempt to read data from the socket connection

        :param rx_queue Queue for pushing data read from the socket onto
        :param connection Socket connection to read data from
        :param should_run Event to check on each loop to determine if to continue reading
        :type rx_queue threading.Queue
        :type connection SocketConnection
        :type should_run threading.Event
        :return: None
        """
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

    def _connection_thread_message_writer(self, tx_queue, connection, should_run):
        """This method is designed to be run in a thread, it will loop infinitely as long as should_run.is_set()
        returns True. In its loop it will attempt to write pending data from the socket connection

        :param tx_queue Queue for pulling data to be written to the socket
        :param connection Socket connection to write data to
        :param should_run Event to check on each loop to determine if to continue writing
        :type tx_queue threading.Queue
        :type connection SocketConnection
        :type should_run threading.Event
        :return: None
        """
        Logger.info('SocketComm: connection thread message writer started')
        while should_run.is_set():
            try:
                message = tx_queue.get(True, 1.0)
                if message:
                    Logger.debug("SocketComm: writing message {}".format(message))
                    connection.write(message)
            except Empty:
                pass
            except Exception as e:
                Logger.error('SocketComm: Exception in connection_thread_message_writer ' + str(e))
                Logger.debug(traceback.format_exc())
                should_run.clear()
                sleep(0.5)
        Logger.debug('SocketComm: connection thread message writer exited')

    def _connection_message_thread(self, connection, address, rx_queue, tx_queue, command_queue):
        """
        'Manager' method that is run in a thread that starts up the read and write threads for the socket
         connection. Watches the command_queue to know when to stop

        :param connection: Socket connection
        :param address: IP address to connect to
        :param rx_queue: Receive queue
        :param tx_queue: Transmit queue
        :param command_queue: Command queue
        :return: None
        """
        Logger.info('SocketComm: connection process starting')

        try:
            connection.open(address)
            connection.flushInput()
            connection.flushOutput()

            reader_writer_should_run = threading.Event()
            reader_writer_should_run.set()

            reader_thread = threading.Thread(target=self._connection_thread_message_reader, args=(rx_queue, connection,
                                                                                            reader_writer_should_run))
            reader_thread.start()

            writer_thread = threading.Thread(target=self._connection_thread_message_writer, args=(tx_queue, connection,
                                                                                            reader_writer_should_run))
            writer_thread.start()

            while reader_writer_should_run.is_set():
                try:
                    command = command_queue.get(True, self.KEEP_ALIVE_TIMEOUT_S)
                    if command == self.COMMAND_CLOSE:
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

