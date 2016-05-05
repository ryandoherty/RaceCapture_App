from kivy.logger import Logger
import socket

class SocketConnection():

    def __init__(self, **kwargs):
        self.socket = None
        pass
    
    def get_available_ports(self):
        # Listen for UDP beacon from RC wifi
        return []

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
