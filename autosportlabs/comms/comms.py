from threading import Thread, RLock, Event
from autosportlabs.racecapture.config.rcpconfig import VersionConfig
from time import sleep

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
    
    def autoDetect(self, getVersion, winCallback, failCallback):
        self.getVersion = getVersion
        t = Thread(target=self.autoDetectWorker, args=(getVersion, winCallback, failCallback))
        t.daemon = True
        t.start()        
        
        
        
    def autoDetectWorker(self, getVersion, winCallback = None, failCallback = None):

        class VersionResult(object):
            version_json = None

        def on_ver_win(value):
            print('get_ver_success ' + str(value))
            version_result.version_json = value
            version_result_event.set()
            
        def on_ver_fail(value):
            print('on_ver_fail ' + str(value))
            version_result_event.set()
        
        
        version_result = VersionResult()        
        version_result_event = Event()
        version_result_event.clear()
            
        if self.port:
            ports = [self.port]
        else:
            ports = self.connection.get_available_ports()

        self.retryCount = 0
        self.timeout = 0.5
        self.writeTimeout = 0
        print "Searching for device on all ports"
        testVer = VersionConfig()
        for p in ports:
            try:
                print "Trying", p
                self.port = p
                self.open()
                getVersion(on_ver_win, on_ver_fail)
                version_result_event.wait()
                version_result_event.clear()
                if version_result.version_json != None:
                    print('get ver success!')
                    testVer.fromJson(version_result.version_json.get('ver', None))
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
        if version_result.version_json != None:
            print "Found device version " + testVer.toString() + " on port:", self.port
            self.close()
            print("sleeping before re-opeining")
            #sleep(5)
            #self.open()
            if winCallback: winCallback(testVer)
        else:
            self.port = None
            if failCallback: failCallback()
        
        while True:
            sleep(1)
            print("zzzzzzzzzzzzzzzzzzzzz")
        
        print("Autodetect worker exiting")
