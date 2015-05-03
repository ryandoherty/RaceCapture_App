from jnius import autoclass

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
UUID = autoclass('java.util.UUID')

class PortNotOpenException(Exception):
    pass

class CommsErrorException(Exception):
    pass

class BluetoothConnection(object):
    ser = None
    recv_stream = None
    send_stream = None
    socket = None
    error_message = None
    
    def __init__(self, **kwargs):
        pass
            
    def get_available_ports(self):
        return ['RaceCapturePro']
                
    def isOpen(self):
        return self.socket != None
    

    def open(self, port):
        error_message = None
        
        try:
            paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
            socket = None
            print('attempting to open port::: ' + port)
            for device in paired_devices:
                if device.getName() == port:
                    print('waiting to connect to device ' + port)
                    socket = device.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                    print('after wait')
                    recv_stream = socket.getInputStream()
                    send_stream = socket.getOutputStream()
                    break
            if socket != None:
                print('attempting to connect socket')
                socket.connect()
                print('socket connected')                    
                self.socket = socket
                self.recv_stream = recv_stream
                self.send_stream = send_stream
                error_message = None
            else:
                error_message = 'Could not detect device {}'.format(port)
        except Exception as e:
            print('error opening socket ' + str(e))
            error_message = 'Error opening Bluetooth socket: {}'.format(str(e))

        if error_message != None:
            raise Exception(error_message)
        if self.socket == None:
            raise Exception("Timed out opening Bluetooth port")
                                    
    def close(self):
        try:
            self.socket.close()
        except Exception as e:
            print('Error closing Bluetooth socket: ' + str(e))
        finally:
            self.socket = None
            self.recv_stream = None
            self.send_stream = None


    def read(self, count):
        recv_stream = self.recv_stream
        if recv_stream == None: raise PortNotOpenException()
        c = recv_stream.read()
        if c == -1:
            self.close()
            raise Exception('Socket reported EOF')
        else:
            return chr(c)

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
            self.send_stream.write(data)
        except Exception as e:
            print('write error; stream not active ' + str(e))
            raise
    
    def flushInput(self):
        pass
    
    def flushOutput(self):
        self.send_stream.flush()
