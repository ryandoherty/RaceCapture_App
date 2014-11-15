import termios
import serial
from serial import SerialException
from serial.tools import list_ports
from autosportlabs.comms.comms import PortNotOpenException, CommsErrorException

class SerialConnection():
    DEFAULT_WRITE_TIMEOUT = 1
    DEFAULT_READ_TIMEOUT = 1
    timeout = DEFAULT_READ_TIMEOUT
    writeTimeout = DEFAULT_WRITE_TIMEOUT 
    
    ser = None
    
    def __init__(self, **kwargs):
        pass
    
    def get_available_ports(self):
        ports = [x[0] for x in list_ports.comports()]
        return ports
            
    def isOpen(self):
        return self.ser != None
    
    def open(self, port):
        ser = serial.Serial(port, timeout=self.timeout, writeTimeout = self.writeTimeout) 
        self.ser = ser
            
    def close(self):
        if self.ser != None:
            self.ser.close()
        self.ser = None

    def read(self, count):
        ser = self.ser
        if ser == None: raise PortNotOpenException()
        try:
            return ser.read(count)
        except termios.error:
            raise CommsErrorException()
        except SerialException as e:
            if str(e).startswith('device reports readiness'):
                return ''
            else: 
                raise
    
    def read_line(self):
        msg = ''
        while True:
            c = self.read(1)
            if c == '':
                return None
            msg += c
            if msg[-2:] == '\r\n':
                msg = msg[:-2]
                return msg
    
    def write(self, data):
        try:
            return self.ser.write(data)
        except termios.error:
            raise CommsErrorException()
            
    
    def flushInput(self):
        try:
            self.ser.flushInput()
        except termios.error:
            raise CommsErrorException()
    
    def flushOutput(self):
        try:
            self.ser.flushOutput()
        except termios.error:
            raise CommsErrorException()
