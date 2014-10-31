import serial
from serial.tools import list_ports

class SerialConnection():
    ser = None
    
    def __init__(self, **kwargs):
        pass

    
    def get_available_ports(self):
        ports = [x[0] for x in list_ports.comports()]
        return ports
    
    def reset(self):
        self.close()
        self.ser = None
        
    def isOpen(self):
        return not self.ser == None
    
    def open(self, port, timeout, writeTimeout):
        if port: self.port = port
        if self.port == None:
            raise Exception("Error opening: port is not defined")
        
        ser = serial.Serial(self.port, timeout=timeout, writeTimeout = writeTimeout) 
        self.ser = ser
            
    def close(self):
        print('closing serial')
        if self.ser != None:
            self.ser.close()
        self.ser = None

    def read(self, count):
        return self.ser.read(count)
    
    def write(self, data):
        return self.ser.write(data)
    
    def flushInput(self):
        self.ser.flushInput()
    
    def flushOutput(self):
        self.ser.flushOutput()
