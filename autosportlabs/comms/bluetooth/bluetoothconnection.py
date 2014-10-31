
class SerialConnection():
    ser = None
    
    def __init__(self, **kwargs):
        pass
    
    def get_available_ports(self):
        pass
        
    def reset(self):
        self.close()
        
    def isOpen(self):
        pass
    
    def open(self, port, timeout, writeTimeout):
        pass
            
    def close(self):
        pass

    def read(self, count):
        pass
    
    def write(self, data):
        pass
    
    def flushInput(self):
        pass
    
    def flushOutput(self):
        pass























__version__ = "1.0.0"
# Same as before, with a kivy-based UI
 
'''
Bluetooth/Pyjnius example
=========================
 
This was used to send some bytes to an arduino via bluetooth.
The app must have BLUETOOTH and BLUETOOTH_ADMIN permissions (well, i didn't
tested without BLUETOOTH_ADMIN, maybe it works.)
 
Connect your device to your phone, via the bluetooth menu. After the
pairing is done, you'll be able to use it in the app.
'''
 
from jnius import autoclass
from threading import Thread, RLock
 
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')
 
def get_socket_stream(name):
    paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
    socket = None
    for device in paired_devices:
        if device.getName() == name:
            socket = device.createRfcommSocketToServiceRecord(
                UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
            recv_stream = socket.getInputStream()
            send_stream = socket.getOutputStream()
            break
    socket.connect()
    return recv_stream, send_stream
 
if __name__ == '__main__':
    kv = '''
BoxLayout:
    orientation: 'vertical'
    TextInput:
        id: textTx
        multiline: True
    BoxLayout:
        orientation: 'horizontal'
        Button:
            text: 'Send'
            on_release: app.send(textTx.text)
        Button:
            text: 'Clear'
            on_release: textRx.text = ''
    TextInput:
        id: textRx
        multiline: True        
    '''
    from kivy.lang import Builder
    from kivy.app import App
    from kivy.clock import Clock
    
    class Bluetooth(App):
        
        rx_line = ''
        
        def build(self):
            self.recv_stream, self.send_stream = get_socket_stream('RaceCapturePro')
            res = Builder.load_string(kv)
            t = Thread(target=self.bt_rx_worker)
            t.daemon = True
            t.start()
            return res        

        def bt_rx_worker(self):
            line = ''
            while True:
                c = self.recv_stream.read()
                if c != -1:
                    c = chr(c)
                    line += c
                    if c == '\n':
                        print('rec: ' + line)
                        line = ''
                        self.rx_line = line
                        Clock.schedule_once(self.update_rx)
             
        def update_rx(self, dt):
            self.ids.textRx.text = self.rx_line
            
        def send(self, msg):
            print('sending: ' + msg)
            self.send_stream.write('{}\r\n'.format(msg))
            self.send_stream.flush()
  
    Bluetooth().run()
