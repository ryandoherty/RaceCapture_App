from kivy.logger import Logger
import socket
import json

PORT = 7223
READ_TIMEOUT = 1
SCAN_TIMEOUT = 3

class SocketConnection():

    def __init__(self):
        self.socket = None
        pass
    
    def get_available_devices(self):
        Logger.info("SocketConnection: listening for RC wifi...")
        # Listen for UDP beacon from RC wifi
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(SCAN_TIMEOUT)

        # Bind the socket to the port
        server_address = ('0.0.0.0', PORT)
        sock.bind(server_address)

        # Look for RC hardware for 3 seconds
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
        return False

    def open(self, address):
        # Connect to ip address here
        rc_address = (address, 7223)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(rc_address)
        self.socket.settimeout(READ_TIMEOUT)

    def close(self):
        self.socket.close()

    def read(self, keep_reading):
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
        self.socket.sendall(data)

    def flushInput(self):
        pass
    
    def flushOutput(self):
        pass
