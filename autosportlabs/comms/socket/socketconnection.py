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
import socket
import json

PORT = 7223
READ_TIMEOUT = 1
SCAN_TIMEOUT = 3


class SocketConnection(object):

    def __init__(self):
        self.socket = None

    def get_available_devices(self):
        """
        Listens for RC WiFi's UDP beacon, if found it returns the ips that the RC wifi beacon says it's available on
        :return: List of ip addresses
        """
        Logger.info("SocketConnection: listening for RC wifi...")
        # Listen for UDP beacon from RC wifi
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(SCAN_TIMEOUT)

        # Bind the socket to the port
        server_address = ('0.0.0.0', PORT)
        sock.bind(server_address)

        try:
            data, address = sock.recvfrom(4096)

            if data:
                Logger.info("SocketConnection: got UDP data {}".format(data))
                message = json.loads(data)
                if message['beacon'] and message['beacon']['ip']:
                    sock.close()
                    return message['beacon']['ip']
        except socket.timeout:
            sock.close()
            Logger.info("SocketConnection: found no RC wifi (timeout listening for UDP beacon)")
            return []

    def isOpen(self):
        """
        Returns True or False if socket is open or not
        :return: Boolean
        """
        return self.socket is not None

    def open(self, address):
        """
        Opens a socket connection to the specified address
        :param address: IP address to connect to
        :return: None
        """
        # Connect to ip address here
        rc_address = (address, 7223)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(rc_address)
        self.socket.settimeout(READ_TIMEOUT)

    def close(self):
        """
        Closes the socket connection
        :return: None
        """
        self.socket.close()
        self.socket = None

    def read(self, keep_reading):
        """
        Reads data from the socket. Will continue to read until either "\r\n" is found in the data read from the
        socket or keep_reading.is_set() returns false
        :param keep_reading: Event object that is checked while data is read
        :type keep_reading: threading.Event
        :return: String or None
        """
        msg = ''
        Logger.info("SocketConnection: reading...")

        while keep_reading.is_set():
            try:
                data = self.socket.recv(4096)
                if data == '':
                    return None

                msg += data

                if msg[-2:] == '\r\n':
                    if msg != '':
                        Logger.info("SocketConnection: returning data {}".format(msg))
                        return msg
                    else:
                        return None
            except socket.timeout:
                pass

    def write(self, data):
        """
        Writes data to the socket
        :param data: Data to write
        :type data: String
        :return: None
        """
        self.socket.sendall(data)

    def flushInput(self):
        pass
    
    def flushOutput(self):
        pass
