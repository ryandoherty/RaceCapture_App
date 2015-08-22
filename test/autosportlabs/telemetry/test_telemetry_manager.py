import unittest
from mock import patch
import mock
import socket
from autosportlabs.telemetry.telemetryconnection import *
from autosportlabs.racecapture.databus.databus import DataBusFactory, DataBusPump, DataBus
import asyncore
#from kivy.logger import Logger
#Logger.setLevel(51)  # Hide all Kivy Logger calls

@patch.object(asyncore, 'loop')
@patch('autosportlabs.telemetry.telemetryconnection.TelemetryConnection', autospec=True)
@patch('autosportlabs.racecapture.databus.databus.DataBus')
class TelemetryManagerTest(unittest.TestCase):

    def test_no_start(self, mock_data_bus_pump, mock_telemetry_connection, mock_asyncore):
        data_bus = mock_data_bus_pump()
        device_id = "ADER45"
        host = 'foobar.com'
        port = 5555

        telemetry_manager = TelemetryManager(data_bus, device_id=device_id, host=host, port=port)
        telemetry_manager.start()
        self.assertFalse(mock_telemetry_connection.called, "Does not connect if no meta")

        telemetry_manager = TelemetryManager(data_bus, host=host, port=port)
        telemetry_manager._on_meta({
            'Foo': 'bar',
            'Bar': 'baz',
            'Fizz': 'buzz'
        })
        telemetry_manager.start()
        self.assertFalse(mock_telemetry_connection.called, "Does not connect if no device id")

    @patch('autosportlabs.telemetry.telemetryconnection.threading.Thread')
    def test_auto_start(self, mock_thread, mock_data_bus_pump, mock_telemetry_connection, mock_asyncore):
        data_bus = mock_data_bus_pump()
        device_id = "ADER45"
        host = 'foobar.com'
        port = 5555

        telemetry_manager = TelemetryManager(data_bus, device_id=device_id, host=host, port=port,
                                             auto_start=True)
        telemetry_manager._on_meta({
            'Foo': 'bar',
            'Bar': 'baz',
            'Fizz': 'buzz'
        })

        args, kwargs = mock_telemetry_connection.call_args
        host_arg, port_arg, device_id_arg, meta_arg, bus_arg, status_arg = args

        self.assertEqual(host_arg, host, "Host is passed to TelemetryConnection")
        self.assertEqual(port_arg, port, "Port is passed to TelemetryConnection")

        self.assertTrue(mock_telemetry_connection.called, "Connects automatically")
        self.assertTrue(telemetry_manager._connection_process.start.called, "Telemetry connection started")

    @patch('autosportlabs.telemetry.telemetryconnection.threading.Timer')
    def test_reconnect(self, mock_timer, mock_data_bus_pump, mock_telemetry_connection, mock_asyncore):
        mock_telemetry_connection.STATUS_DISCONNECTED = 0

        data_bus = mock_data_bus_pump()
        device_id = "ADER45"
        host = 'foobar.com'
        port = 5555

        telemetry_manager = TelemetryManager(data_bus, device_id=device_id, host=host, port=port,
                                             auto_start=True)
        telemetry_manager._on_meta({
            'Foo': 'bar',
            'Bar': 'baz',
            'Fizz': 'buzz'
        })

        self.assertTrue(mock_telemetry_connection.called)
        telemetry_manager.status("error", "Disconnected", TelemetryConnection.STATUS_DISCONNECTED)

        args, kwargs = mock_timer.call_args
        timeout, connect = args

        self.assertEqual('_connect', connect.__name__)
        self.assertEqual(TelemetryManager.RETRY_WAIT, timeout)

        self.assertTrue(mock_timer.called)

