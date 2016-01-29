import serial
from serial import SerialException
from serial.tools import list_ports
from autosportlabs.comms.commscommon import PortNotOpenException, CommsErrorException
from kivy.logger import Logger

class SerialConnection():
    DEFAULT_WRITE_TIMEOUT = 3
    DEFAULT_READ_TIMEOUT = 1
    timeout = DEFAULT_READ_TIMEOUT
    writeTimeout = DEFAULT_WRITE_TIMEOUT

    ser = None

    def __init__(self, **kwargs):
        pass

    def get_available_ports(self):
        Logger.debug("SerialConnection: getting available ports")
        ports = [x[0] for x in list_ports.comports()]
        ports.sort()
        filtered_ports = filter(lambda port: not port.startswith('/dev/ttyUSB') and not port.startswith('/dev/ttyS') and not port.startswith('/dev/cu.Bluetooth-Incoming-Port'), ports)
        return filtered_ports

    def isOpen(self):
        return self.ser != None

    def open(self, port):
        ser = serial.Serial(port, baudrate=115200, timeout=self.timeout, \
                            write_timeout = self.writeTimeout)
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
        except SerialException as e:
            raise CommsErrorException(cause=e)


    def flushInput(self):
        try:
            self.ser.flushInput()
        except SerialException as e:
            raise CommsErrorException(cause=e)

    def flushOutput(self):
        try:
            self.ser.flushOutput()
        except SerialException as e:
            raise CommsErrorException(cause=e)
