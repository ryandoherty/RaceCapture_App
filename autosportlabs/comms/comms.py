from threading import Thread, RLock
from autosportlabs.racecapture.config.rcpconfig import VersionConfig

class Comms():
    DEFAULT_READ_RETRIES = 2
    DEFAULT_WRITE_TIMEOUT = 1
    DEFAULT_READ_TIMEOUT = 1
    getVersion = None
    port = None
    connection = None
    timeout = DEFAULT_READ_TIMEOUT
    writeTimeout = DEFAULT_WRITE_TIMEOUT 

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
    
    def isOpen(self):
        return self.connection.isOpen()
    
    def open(self):
        connection = self.connection
        print('Opening connection')
        if self.port == None:
            self.autoDetectWorker(self.getVersion)
            if self.port == None:
                connection.close()
                raise Exception('Could not open connection: Device not detected')
        else:
            if self.timeout == None:
                raise Exception("No timeout")
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
            if  c == eol2:
                break
            elif c == '':
                print('empty character received...')
                if retryCount >= self.retryCount:
                    self.close()
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
    
    def autoDetect(self, getVersion, winCallback, failCallback):
        self.getVersion = getVersion
        t = Thread(target=self.autoDetectWorker, args=(getVersion, winCallback, failCallback))
        t.daemon = True
        t.start()        
        
    def autoDetectWorker(self, getVersion, winCallback = None, failCallback = None):
        if self.port:
            ports = [self.port]
        else:
            ports = self.connection.get_available_ports()

        self.retryCount = 0
        self.timeout = 0.5
        self.writeTimeout = 0
        print "Searching for device on all ports"
        testVer = VersionConfig()
        verJson = None
        for p in ports:
            try:
                print "Trying", p
                self.port = p
                self.open()
                verJson = getVersion(True)
                testVer.fromJson(verJson.get('ver', None))
                if testVer.major > 0 or testVer.minor > 0 or testVer.bugfix > 0:
                    break
                
            except Exception as detail:
                print('Not found on ' + str(p) + " " + str(detail))
                try:
                    self.close()
                    self.port = None
                finally:
                    pass

        self.retryCount = self.DEFAULT_READ_RETRIES
        self.timeout = self.DEFAULT_READ_TIMEOUT
        self.writeTimeout = self.DEFAULT_WRITE_TIMEOUT
        if not verJson == None:
            print "Found device version " + testVer.toString() + " on port:", self.port
            self.close()
            self.open()
            if winCallback: winCallback(testVer)
        else:
            self.port = None
            if failCallback: failCallback()
        
