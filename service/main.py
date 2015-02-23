from time import sleep, time
from kivy.lib import osc
from kivy.logger import Logger
from autosportlabs.comms.bluetooth.bluetoothconnection import BluetoothConnection, PortNotOpenException
from threading import Thread, Event
import traceback
import jnius
import logging

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

KEEP_ALIVE_TIMEOUT      = 30
RX_THREAD_JOIN_DELAY    = 10
OSC_PROCESSING_INTERVAL = 0.01

last_keep_alive_time = time()

def tx_api_callback(message, *args):
    message = message[2]
    bt_connection.write(message)

def cmd_api_callback(message, *args):
    message = message[2]
    if message == 'EXIT':
        Logger.info('RC_SVC: ############################## GOT EXIT CMD #####################################')
        service_should_run.clear()
    elif message == 'OPEN':
        try:
            Logger.info('RC_SVC: ############################## GOT OPEN CMD #####################################')
            bt_connection.open('RaceCapturePro')
        except Exception as e:
            Logger.info("RC_SVC:Failed to open Bluetooth connection: " + str(e))
    elif message == 'CLOSE':
        Logger.info('RC_SVC: ############################## GOT CLOSE CMD #####################################')
        bt_connection.close()
    elif message == 'GET_PORTS':
        Logger.info('RC_SVC: ############################## GOT GET_PORTS CMD #####################################')
        ports = bt_connection.get_available_ports()
        osc.sendMsg(CMD_API, [ports ,], port=CLIENT_API_PORT)
    elif message == 'PING':
        global last_keep_alive_time
        last_keep_alive_time = time();

def bt_rx_thread():
    Logger.info('RC_SVC: ############################## bt_rx_thread started ##############################')
    while service_should_run.is_set():
        try:
            msg = bt_connection.read_line()
            if msg:
                osc.sendMsg(RX_API, [msg, ], port=CLIENT_API_PORT)
        except PortNotOpenException:
            sleep(1.0)
            pass                
        except Exception as e:
            Logger.info('RC_SVC: Exception in rx_message_thread')
            traceback.print_exc()
            osc.sendMsg(CMD_API, ["ERROR", ], port=CLIENT_API_PORT)
            sleep(1.0)
    jnius.detach() #detach the current thread from pyjnius, else hard crash occurs 
    Logger.info('RC_SVC: ############################## bt_rx_thread exited ##############################')
              
if __name__ == '__main__':
    Logger.info('RC_SVC: ############################## Android Service Started ##############################')
    
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
                Logger.warn("RC_SVC: keep alive timeout!")
                service_should_run.clear()
            sleep(OSC_PROCESSING_INTERVAL)
        except Exception as e:
            Logger.error('RC_SVC: Exception in OSC queue processing ' + str(e))
            traceback.print_exc()
            
    osc.dontListen()            
    bt_connection.close()
    bt_thread.join(RX_THREAD_JOIN_DELAY)
    del bt_thread
    Logger.info('RC_SVC: ############################## Android Service Exiting ##############################')
    exit(0) #This is needed else the service hangs around in a zombie like state forever
