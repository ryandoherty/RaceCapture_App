import serial
from serial import SerialException
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
        print('open: ' + str(timeout) + ' ' + str(writeTimeout))
        ser = serial.Serial(port, timeout=timeout, writeTimeout = writeTimeout) 
        self.ser = ser
            
    def close(self):
        print('closing serial')
        if self.ser != None:
            self.ser.close()
        self.ser = None

    def read(self, count):
        try:
            return self.ser.read(count)
        except SerialException as e:
            if str(e).startswith('device reports readiness'):
                return ''
            else: 
                raise
    
    def write(self, data):
        return self.ser.write(data)
    
    def flushInput(self):
        self.ser.flushInput()
    
    def flushOutput(self):
        self.ser.flushOutput()
