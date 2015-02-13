from kivy import platform
if platform == 'android':
    pass
elif platform == 'ios':
    from autosportlabs.comms.socket.socketconnection import SocketConnection
else:
    from autosportlabs.comms.serial.serialconnection import SerialConnection

__all__ = ('comms_factory')

def comms_factory(port):
    if platform == 'android':
        from autosportlabs.comms.androidcomms import AndroidComms
        return AndroidComms(port=port)
    elif platform == 'ios':
        print('iOS comms not implemented yet')
        return None
    else:
        from autosportlabs.comms.comms import Comms        
        return Comms(port=port, connection=SerialConnection())
