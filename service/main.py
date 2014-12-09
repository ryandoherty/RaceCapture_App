from time import sleep
from kivy.lib import osc
from autosportlabs.comms.bluetooth.bluetoothconnection import BluetoothConnection
import threading
import traceback

CMD_API                 = '/rc_cmd'
TX_API                  = '/rc_tx'
RX_API                  = '/rc_rx'

SERVICE_API_PORT        = 3000
CLIENT_API_PORT         = 3001

SERVICE_CMD_EXIT        = 'EXIT'
SERVICE_CMD_OPEN        = 'OPEN'
SERVICE_CMD_CLOSE       = 'CLOSE'
SERVICE_CMD_GET_PORTS   = 'GET_PORTS'

def tx_api_callback(message, *args):
    print('service tx received: ' + str(message))
    bt_connection.write(message)

def cmd_api_callback(message, *args):
    print('service command received: ' + str(message))
    if message == 'EXIT':
        service_should_run.clear()
    elif message == 'OPEN':
        bt_connection.open(args[0])
    elif message == 'CLOSE':
        bt_connection.close()
    elif message == 'GET_PORTS':
        ports = bt_connection.get_available_ports()
        osc.sendMsg(CMD_API, [ports ,], port=CLIENT_API_PORT)

def osc_queue_processor_thread(should_run):
    print('osc_queue_processor_thread started')
    while should_run.is_set():
        try:
            osc.readQueue(oscid)
            sleep(0.1)
        except Exception as e:
            print('Exception in osc_queue_processor_thread ' + str(e))
            traceback.print_exc()
            sleep(0.5)
    print('osc_queue_processor_thread exited')

def rx_message_thread(should_run):
    print('rx_message_thread started')
    
    while should_run.is_set():
        try:
            msg = bt_connection.read_line()
            if msg:
                osc.sendMsg(RX_API, [msg, ], port=CLIENT_API_PORT)
            print('bt read_line ' + str(msg))                
        except:
            print('Exception in rx_message_thread')
            traceback.print_exc()
            #_rx_queue.put('##ERROR##')
            sleep(0.5)
    print('rx_message_thread exited')            
      
if __name__ == '__main__':
    bt_connection = BluetoothConnection()
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=SERVICE_API_PORT)
    osc.bind(oscid, tx_api_callback, TX_API)
    osc.bind(oscid, cmd_api_callback, CMD_API)
    
    service_should_run = threading.Event()
    service_should_run.set()

    osc_processor_thread = threading.Thread(target=osc_queue_processor_thread, args=(service_should_run))
    osc_processor_thread.start()
    
    rx_message_thread = threading.Thread(target=rx_message_thread, args=(service_should_run))
    rx_message_thread.start()
