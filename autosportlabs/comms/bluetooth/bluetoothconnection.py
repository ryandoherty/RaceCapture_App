
from jnius import autoclass
from threading import Thread, Event

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')


class BluetoothConnection():
    ser = None
    recv_stream = None
    send_stream = None
    socket = None
    open_request_event = None
    open_complete_event = None
    
    def __init__(self, **kwargs):
        self.open_request_event = Event()
        self.open_complete_event = Event()
        self.open_request_event.clear()
        self.open_complete_event.clear()
        opener_thread = Thread(target=self.rf_comm_socket_opener)
        opener_thread.start()
            
    def get_available_ports(self):
        return ['RaceCapturePro']
        
    def reset(self):
        self.close()
        
    def isOpen(self):
        return self.socket != None
    
    port_to_open = None
    error_message = None

    def open(self, port, timeout, writeTimeout):
        self.port_to_open = port
        self.error_message = None
        self.open_request_event.set()
        print('waiting to open Bluetooth')
        self.open_complete_event.wait(30.0)
        self.open_complete_event.clear()
        print('after waiting for Bluetooth open: ' + str(self.error_message))
        if self.error_message != None:
            raise Exception(self.error_message)
        if self.socket == None:
            raise Exception("Timed out opening Bluetooth port")

    
    def rf_comm_socket_opener(self):
        print('rf_comm_socket_opener starting')
        while True:
            self.open_request_event.wait()
            self.open_request_event.clear()
            try:
                paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
                socket = None
                port = self.port_to_open
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
                    self.error_message = None
                else:
                    self.error_message = 'Could not detect device {}'.format(port)
            except Exception as e:
                print('error opening socket ' + str(e))
                self.error_message = 'Error opening Bluetooth socket: {}'.format(str(e))
            finally:
                self.open_complete_event.set()
        print('Exiting rf_comm_socket_opener')
                            
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
