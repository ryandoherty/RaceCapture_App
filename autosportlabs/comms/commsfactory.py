from kivy import platform

__all__ = 'comms_factory'


def comms_factory(device, conn_type):
    # Connection type can be overridden by user or for testing purposes
    if conn_type is not None:
        if conn_type == 'bluetooth':
            return android_comm(device)
        if conn_type == 'wifi':
            return socket_comm(device)
    else:
        if platform == 'android':
            return android_comm(device)
        elif platform == 'ios':
            return socket_comm(device)
        else:
            return serial_comm(device)


def socket_comm(device):
    from autosportlabs.comms.socket.socketconnection import SocketConnection
    from autosportlabs.comms.socket.socketcomm import SocketComm
    return SocketComm(SocketConnection(), device)


def serial_comm(device):
    from autosportlabs.comms.serial.serialconnection import SerialConnection
    from autosportlabs.comms.comms import Comms
    return Comms(device, SerialConnection())


def android_comm(device):
    from autosportlabs.comms.androidcomms import AndroidComms
    return AndroidComms(device)
