
class SerialConnection():
    ser = None
    
    def __init__(self, **kwargs):
        pass
    
    def get_available_ports(self):
        pass
                
    def isOpen(self):
        pass
    
    def open(self, port, timeout, writeTimeout):
        pass
            
    def close(self):
        pass

    def read(self, count):
        pass
    
    def write(self, data):
        pass
    
    def flushInput(self):
        pass
    
    def flushOutput(self):
        pass
