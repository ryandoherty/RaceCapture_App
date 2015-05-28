import unittest
from autosportlabs.racecapture.databus.filter.laptimedeltafilter import LaptimeDeltaFilter
from autosportlabs.racecapture.data.channels import SystemChannels

class LaptimeDeltaFilterTest(unittest.TestCase):
    system_channels = SystemChannels()
    
    def test_laptime_delta_filter_meta(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        meta = sample_filter.get_channel_meta()
        self.assertIsNotNone(meta.get(LaptimeDeltaFilter.LAP_DELTA_KEY))
        
    def test_laptime_delta_default(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        channel_data = {}
        sample_filter.filter(channel_data)
        self.assertEqual(0.0, channel_data.get(LaptimeDeltaFilter.LAP_DELTA_KEY))

    def test_laptime_delta_only_laptime(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        channel_data = {LaptimeDeltaFilter.LAPTIME_KEY:1.0,
                        LaptimeDeltaFilter.BEST_LAPTIME_KEY:2.0}
        sample_filter.filter(channel_data)
        self.assertEqual(-1.0, channel_data.get(LaptimeDeltaFilter.LAP_DELTA_KEY))

    def test_laptime_delta_only_predtime(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        channel_data = {LaptimeDeltaFilter.PREDTIME_KEY:1.0,
                        LaptimeDeltaFilter.BEST_LAPTIME_KEY:2.0}
        sample_filter.filter(channel_data)
        self.assertEqual(-1.0, channel_data.get(LaptimeDeltaFilter.LAP_DELTA_KEY))

    def test_laptime_delta_predtime_and_laptime_present(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        channel_data = {LaptimeDeltaFilter.PREDTIME_KEY:3.0,
                        LaptimeDeltaFilter.LAPTIME_KEY:1.0,
                        LaptimeDeltaFilter.BEST_LAPTIME_KEY:2.0}
        sample_filter.filter(channel_data)
        self.assertEqual(1.0, channel_data.get(LaptimeDeltaFilter.LAP_DELTA_KEY))
        