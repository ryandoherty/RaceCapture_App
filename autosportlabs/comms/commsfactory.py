from kivy import platform
if platform == 'android':
    from autosportlabs.comms.bluetooth.bluetoothconnection import BluetoothConnection
elif platform == 'ios':
    from autosportlabs.comms.socket.socketconnection import SocketConnection
else:
    from autosportlabs.comms.serial.serialconnection import SerialConnection

__all__ = ('comms_factory')

def comms_factory(port):
    if platform == 'android':
        from autosportlabs.comms.androidcomms import AndroidComms
        return AndroidComms(port=port, connection=BluetoothConnection())
    elif platform == 'ios':
        return AndroidComms(port=port, connection=SocketConnection())
    else:
        from autosportlabs.comms.comms import Comms        
        return Comms(port=port, connection=SerialConnection())
