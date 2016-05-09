from kivy.logger import Logger

class SocketConnection():

    def __init__(self, **kwargs):
        pass
    
    def get_available_ports(self):
        return []

    def isOpen(self):
        return False

    def open(self, port):
        pass
            
    def close(self):
        pass

    def read(self, count):
        pass

    def read_line(self):
        return ''
    
    def write(self, data):
        pass
    
    def flushInput(self):
        pass
    
    def flushOutput(self):
        pass
