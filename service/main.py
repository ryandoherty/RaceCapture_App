from time import sleep, time
from kivy.lib import osc
from autosportlabs.comms.bluetooth.bluetoothconnection import BluetoothConnection, PortNotOpenException
from threading import Thread, Event
import traceback
import jnius

CMD_API                 = '/rc_cmd'
TX_API                  = '/rc_tx'
RX_API                  = '/rc_rx'

SERVICE_API_PORT        = 3000
CLIENT_API_PORT         = 3001

SERVICE_CMD_EXIT        = 'EXIT'
SERVICE_CMD_OPEN        = 'OPEN'
SERVICE_CMD_CLOSE       = 'CLOSE'
SERVICE_CMD_KEEP_ALIVE  = 'PING'
SERVICE_CMD_GET_PORTS   = 'GET_PORTS'

KEEP_ALIVE_TIMEOUT = 30
OSC_THREAD_JOIN_DELAY = 10
OSC_THREAD_EXIT_DELAY = 5

last_keep_alive_time = time()

def tx_api_callback(message, *args):
    message = message[2]
    bt_connection.write(message)
    jnius.detach()

def cmd_api_callback(message, *args):
    message = message[2]
    if message == 'EXIT':
        print("###############GOT EXIT CMD######################")
        service_should_run.clear()
    elif message == 'OPEN':
        try:
            bt_connection.open('RaceCapturePro')
        except Exception as e:
            print("Failed to open Bluetooth connection: " + str(e))
    elif message == 'CLOSE':
        print("###############GOT CLOSE CMD######################")
        bt_connection.close()
    elif message == 'GET_PORTS':
        ports = bt_connection.get_available_ports()
        osc.sendMsg(CMD_API, [ports ,], port=CLIENT_API_PORT)
    elif message == 'PING':
        global last_keep_alive_time
        last_keep_alive_time = time();
    jnius.detach()        

def bt_rx_thread():
    print('bt_rx_thread started')
    while service_should_run.is_set():
        try:
            msg = bt_connection.read_line()
            if msg:
                osc.sendMsg(RX_API, [msg, ], port=CLIENT_API_PORT)
        except PortNotOpenException:
            sleep(1.0)
            pass                
        except Exception as e:
            print('Exception in rx_message_thread')
            traceback.print_exc()
            osc.sendMsg(CMD_API, ["ERROR", ], port=CLIENT_API_PORT)
            sleep(1.0)
    jnius.detach()
    print('################ bt_rx_thread exited ################')
              
if __name__ == '__main__':
    print("#####################Android Service Started############################")
    
    bt_connection = BluetoothConnection()
    
    service_should_run = Event()
    service_should_run.set()

    bt_thread = Thread(target=bt_rx_thread)
    bt_thread.start()
    
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=SERVICE_API_PORT)
    osc.bind(oscid, tx_api_callback, TX_API)
    osc.bind(oscid, cmd_api_callback, CMD_API)
    global last_keep_alive_time
    while service_should_run.is_set():
        try:
            osc.readQueue(oscid)
            if time() > last_keep_alive_time + KEEP_ALIVE_TIMEOUT:
                print("keep alive timeout!")
                service_should_run.clear()
            sleep(0.01)
        except Exception as e:
            print('Exception in osc_queue_processor_thread ' + str(e))
            traceback.print_exc()
            sleep(0.5)
    osc.dontListen(oscid)            
    bt_connection.close()
    bt_thread.join(5)
    
    print('#####################Android Service Exiting############################')
