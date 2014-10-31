
from jnius import autoclass
 
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')


class SerialConnection():
    ser = None
    recv_stream = None
    send_stream = None
    socket = None
    
    def __init__(self, **kwargs):
        pass
    
    def get_available_ports(self):
        return 'RaceCapturePro'
        
    def reset(self):
        self.close()
        
    def isOpen(self):
        return self.socket != None
    
    def open(self, port, timeout, writeTimeout):
        paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
        socket = None
        for device in paired_devices:
            if device.getName() == port:
                socket = device.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                recv_stream = socket.getInputStream()
                send_stream = socket.getOutputStream()
                break
        if socket == None:
            raise Exception('Could not detect device ' + port)
        
        socket.connect()
        self.socket = socket
        self.recv_stream = recv_stream
        self.send_stream = send_stream
            
    def close(self):
        try:
            self.socket.close()
            self.socket = None
            self.recv_stream = None
            self.send_stream = None
        except Exception as e:
            print('Error closing Bluetooth socket: ' + str(e))

    def read(self, count):
        c = self.recv_stream.read()
        if c == -1:
            self.close()
            raise Exception('Socket reported EOF')
        else:
            return chr(c)
    
    def write(self, data):
        self.send_stream.write(data)
    
    def flushInput(self):
        pass
    
    def flushOutput(self):
        self.send_stream.flush()
