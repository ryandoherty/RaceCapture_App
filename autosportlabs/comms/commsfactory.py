from kivy import platform
if platform == 'android':
    pass
elif platform == 'ios':
    from autosportlabs.comms.socket.socketconnection import SocketConnection
else:
    from autosportlabs.comms.serial.serialconnection import SerialConnection

__all__ = ('comms_factory')

def comms_factory(device):
    if platform == 'android':
        from autosportlabs.comms.androidcomms import AndroidComms
        return AndroidComms(device)
    elif platform == 'ios':
        from autosportlabs.comms.socket.socketconnection import SocketConnection
        from autosportlabs.comms.socket.socketcomm import SocketComm
        return SocketComm(SocketConnection(), device)
    else:
        from autosportlabs.comms.comms import Comms
        return Comms(device, SerialConnection())
