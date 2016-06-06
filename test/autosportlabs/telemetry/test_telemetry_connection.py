import unittest
from mock import patch
import mock
import socket
from autosportlabs.telemetry.telemetryconnection import TelemetryConnection, TelemetryManager
from autosportlabs.util.threadutil import ThreadSafeDict
import asyncore
import json
import random
from kivy.logger import Logger
Logger.setLevel(51)  # Hide all Kivy Logger calls

@patch.object(asyncore, 'loop')
class TelemetryConnectionTest(unittest.TestCase):

    def setUp(self):
        self.host = 'foobar.baz'
        self.port = 8080
        self.device_id = 'DFDS44'

        self.meta = ThreadSafeDict()
        self.meta['foo'] = mock.Mock(units="F", sampleRate="10", min=0, max=100)
        self.meta['bar'] = mock.Mock(units="C", sampleRate="1", min=-100, max=200)
        self.meta['baz'] = mock.Mock(units="C", sampleRate="1", min=-100, max=200)

        # Mock's constructor treats 'name' in a special way, it won't return a string
        self.meta['foo'].configure_mock(name='foo')
        self.meta['bar'].configure_mock(name='bar')
        self.meta['baz'].configure_mock(name='baz')

        self.data_bus = None
        self.telemetry_connection = None

        self.status_function = mock.Mock()
        self.data_bus = mock.Mock()
        self.telemetry_connection = TelemetryConnection(self.host, self.port, self.device_id, self.meta, self.data_bus, self.status_function)

        # We mock these functions because we don't want to really connect to anything
        # This is a unit test, not integration!
        self.telemetry_connection.create_socket = mock.Mock()
        self.telemetry_connection.connect = mock.Mock()
        self.telemetry_connection.push = mock.Mock()

    def test_run(self, asyncore_loop_mock):
        self.telemetry_connection.run()

        self.telemetry_connection.create_socket.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)
        self.telemetry_connection.connect.assert_called_with((self.host, self.port))

        self.assertTrue(asyncore_loop_mock.called)
        self.assertTrue(self.data_bus.add_sample_listener.called)
        self.assertTrue(self.data_bus.addMetaListener.called)

    def test_sends_auth(self, asyncore_loop_mock):
        self.telemetry_connection.run()

        self.telemetry_connection.handle_connect()

        self.telemetry_connection.push.assert_called_with('{"cmd":{"schemaVer":2,"auth":{"deviceId":"' + self.device_id + '"}}}' + "\n")

    def test_sends_authorized_status(self, asyncore_loop_mock):
        self.telemetry_connection.run()
        self.telemetry_connection.handle_connect()

        args, kwargs = self.status_function.call_args
        status, message, status_code = args
        self.assertEqual(status_code, TelemetryConnection.STATUS_CONNECTED)

        self.telemetry_connection.collect_incoming_data('{"status":"ok"}')
        self.telemetry_connection.found_terminator()

        args, kwargs = self.status_function.call_args
        status, message, status_code = args

        self.assertEqual(status_code, TelemetryConnection.STATUS_STREAMING)

    def test_sends_error_authenticating_status(self, asyncore_loop_mock):

        self.telemetry_connection.run()
        self.telemetry_connection.handle_connect()

        self.telemetry_connection.collect_incoming_data('{"status":"error","message":"invalid serial number"}')
        self.telemetry_connection.found_terminator()

        args, kwargs = self.status_function.call_args
        status, message, status_code = args

        self.assertEqual(status_code, TelemetryConnection.ERROR_AUTHENTICATING)

    def test_sends_unknown_error(self, asyncore_loop_mock):
        self.telemetry_connection.run()
        self.telemetry_connection.handle_connect()

        self.telemetry_connection.collect_incoming_data('{"foo":"bar"}')
        self.telemetry_connection.found_terminator()

        args, kwargs = self.status_function.call_args
        status, message, status_code = args

        self.assertEqual(status_code, TelemetryConnection.ERROR_UNKNOWN_MESSAGE)

    def test_sends_meta(self, asyncore_loop_mock):
        self.telemetry_connection.run()
        self.telemetry_connection.handle_connect()

        args, kwargs = self.status_function.call_args
        status, message, status_code = args
        self.assertEqual(status_code, TelemetryConnection.STATUS_CONNECTED)

        self.telemetry_connection.collect_incoming_data('{"status":"ok"}')
        self.telemetry_connection.found_terminator()

        args, kwargs = self.telemetry_connection.push.call_args
        message, = args

        meta_json = json.loads(message)

        self.assertTrue("s" in meta_json, "Sends 's'")
        self.assertTrue("meta" in meta_json["s"], "Sends meta property")

        for name, info in self.meta.iteritems():
            # Verify all the channels were sent with correct info
            channel_info = next((item for item in meta_json["s"]["meta"] if item["nm"] == name), None)

            self.assertIsNotNone(channel_info, "Channel found")

            self.assertEqual(channel_info["ut"], info.units, "Units are sent")
            self.assertEqual(channel_info["sr"], info.sampleRate, "Sample rate is sent")
            self.assertEqual(channel_info["min"], info.min, "Min is sent")
            self.assertEqual(channel_info["max"], info.max, "Max is sent")

    def test_sends_line_break(self, asyncore_loop_mock):

        self.telemetry_connection.send_msg("foo")
        args, kwargs = self.telemetry_connection.push.call_args
        message, = args

        self.assertEqual(message, "foo\n", "Newline added to end of message")

    @patch('threading.Timer')
    def test_sends_bitmask(self, timer_mock, asyncore_loop_mock):
        sample = ThreadSafeDict()
        sample['bar'] = 3.0

        bitmask = ''

        # Compute our own bitmask to verify
        for channel_name, value in self.meta.iteritems():
            if channel_name == 'bar':
                bitmask = "1" + bitmask
            else:
                bitmask = "0" + bitmask

        bitmask = int(bitmask, 2)

        self.telemetry_connection._on_sample(sample)
        self.telemetry_connection._send_sample()

        args, kwargs = self.telemetry_connection.push.call_args
        message, = args

        message_json = json.loads(message)

        self.assertEqual(bitmask, message_json["s"]["d"][len(message_json["s"]["d"])-1])

    @patch('threading.Timer')
    def test_sends_multiple_bitmasks(self, timer_mock, asyncore_loop_mock):
        sample = ThreadSafeDict()
        meta = ThreadSafeDict()

        for i in range(1, 40):
            meta['sensor' + str(i)] = mock.Mock(units="F", sampleRate="10",
                                              min=random.randint(-100, 0),
                                              max=random.randint(0, 100))
            meta['sensor' + str(i)].configure_mock(name='sensor' + str(i))

        # Manually doing this to aid debugging if this test breaks
        sample['sensor2'] = random.randint(-50, 50)
        sample['sensor3'] = random.randint(-50, 50)
        sample['sensor4'] = random.randint(-50, 50)
        sample['sensor5'] = random.randint(-50, 50)
        sample['sensor6'] = random.randint(-50, 50)
        sample['sensor7'] = random.randint(-50, 50)
        sample['sensor8'] = random.randint(-50, 50)
        sample['sensor10'] = random.randint(-50, 50)
        sample['sensor11'] = random.randint(-50, 50)
        sample['sensor12'] = random.randint(-50, 50)
        sample['sensor21'] = random.randint(-50, 50)
        sample['sensor25'] = random.randint(-50, 50)
        sample['sensor26'] = random.randint(-50, 50)
        sample['sensor29'] = random.randint(-50, 50)
        sample['sensor33'] = random.randint(-50, 50)
        sample['sensor35'] = random.randint(-50, 50)
        sample['sensor37'] = random.randint(-50, 50)
        sample['sensor38'] = random.randint(-50, 50)
        sample['sensor39'] = random.randint(-50, 50)


        self.telemetry_connection.authorized = True
        self.telemetry_connection._on_meta(meta)

        self.telemetry_connection._on_sample(sample)
        self.telemetry_connection._send_sample()

        args, kwargs = self.telemetry_connection.push.call_args
        message, = args

        message_json = json.loads(message)

        self.assertEqual(19, message_json["s"]["d"][len(message_json["s"]["d"])-1])
        self.assertEqual(1479378921, message_json["s"]["d"][len(message_json["s"]["d"])-2])

    @patch('threading.Timer')
    def resends_meta(self, timer_mock, asyncore_loop_mock):
        meta = {}

        for i in range(1, 5):
            meta['sensor'+str(i)] = mock.Mock(units="F", sampleRate="10",
                                              min=random.randint(-100,0),
                                              max=random.randint(0,100))
            meta['sensor'+str(i)].configure_mock(name='sensor'+str(i))

        self.telemetry_connection._on_meta(meta)

        args, kwargs = self.telemetry_connection.push.call_args
        message, = args

        message_json = json.loads(message)

        self.assertEqual(len(message_json["s"]["meta"]), 5)







