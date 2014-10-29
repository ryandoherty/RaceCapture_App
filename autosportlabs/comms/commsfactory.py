from kivy import platform
if platform == 'android':
    from autosportlabs.comms.bluetooth.bluetoothcomms import *
elif platform == 'ios':
    from autosportlabs.comms.socket.socketcomms import *
else:
    from autosportlabs.comms.serial.serialcomms import Comms

__all__ = ('comms_factory_create')

def comms_factory_create(port):
    return Comms(port=port)