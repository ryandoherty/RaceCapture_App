from threading import Thread, RLock, Event
from time import sleep

class Comms():
    DEFAULT_READ_RETRIES = 2
    DEFAULT_WRITE_TIMEOUT = 1
    DEFAULT_READ_TIMEOUT = 1
    port = None
    connection = None
    timeout = DEFAULT_READ_TIMEOUT
    writeTimeout = DEFAULT_WRITE_TIMEOUT 
    retryCount = DEFAULT_READ_RETRIES    

    def __init__(self, **kwargs):
        self.port = kwargs.get('port')
        self.connection = kwargs.get('connection')
        
    def reset(self):
        self.connection.reset()
        self.port = None
        
    def setPort(self, port):
        self.port = port
    
    def getPort(self):
        return self.port
    
    def get_available_ports(self):
        return self.connection.get_available_ports()
    
    def isOpen(self):
        return self.connection.isOpen()
    
    def open(self):
        connection = self.connection
        print('Opening connection ' + str(self.port))
        connection.open(self.port, timeout=self.timeout, writeTimeout = self.writeTimeout) 
        connection.flushInput()
        connection.flushOutput()
    
    def close(self):
        print('closing connection')
        self.connection.close()

    def read(self, count):
        ret = self.connection.read(count)
        return ret
    
    def readLine(self):
        connection = self.connection
        eol2 = b'\r'
        retryCount = 0
        line = bytearray()

        while True:
            c = connection.read(1)
            print(str(c))
            if  c == eol2:
                break
            elif c == '':
                print('empty character received...')
                if retryCount >= self.retryCount:
                    raise Exception('Could not read line')
                retryCount +=1
                print('Timeout - retry: ' + str(retryCount))
                print("POKE")
                connection.write(' ')
            else:
                line += c
        print('returning line')
        line = bytes(line).strip()
        line = line.replace('\r', '')
        line = line.replace('\n', '')
        return line
    
    def write(self, data):
        return self.connection.write(data)
    
    def flushInput(self):
        self.connection.flushInput()
    
    def flushOutput(self):
        self.connection.flushOutput()
    