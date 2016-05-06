from kivy.logger import Logger
import socket
import json

PORT = 7223

class SocketConnection():

    def __init__(self):
        self.socket = None
        pass
    
    def get_available_devices(self):
        Logger.info("SocketConnection: listening for RC wifi...")
        # Listen for UDP beacon from RC wifi
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind the socket to the port
        server_address = ('0.0.0.0', PORT)
        sock.bind(server_address)

        while True:
            data, address = sock.recvfrom(4096)

            if data:
                Logger.info("SocketConnection: got UDP data {}".format(data))
                message = json.loads(data)
                if message['beacon'] and message['beacon']['ip']:
                    sock.close()
                    return message['beacon']['ip']

    def isOpen(self):
        return False

    def open(self, address):
        # Connect to ip address here
        rc_address = (address, 7223)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(rc_address)

    def close(self):
        self.socket.close()

    def read(self, count):
        pass

    def read_line(self):
        msg = ''
        Logger.info("SocketConnection: reading line...")

        while True:
            data = self.socket.recv(4096)
            if data == '':
                return None

            msg += data

            if msg[-2:] == '\r\n':
                Logger.info("SocketConnection: read_line completed, returning data {}".format(msg))
                return msg

    def write(self, data):
        self.socket.sendall(data)

    def flushInput(self):
        pass
    
    def flushOutput(self):
        pass
