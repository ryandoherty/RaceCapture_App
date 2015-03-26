import unittest
from autosportlabs.racecapture.databus.filter.currentlaptimefilter import CurrentLapTimeFilter
from autosportlabs.racecapture.data.sampledata import SystemChannels

class CurrentLaptimeFilterTest(unittest.TestCase):
    system_channels = SystemChannels()
    
    def test_current_laptime_filter_meta(self):
        sample_filter = CurrentLapTimeFilter(self.system_channels)
        meta = sample_filter.get_channel_meta()
        self.assertIsNotNone(meta.get(CurrentLapTimeFilter.CURRENT_LAPTIME_KEY))
            
    def test_laptime_delta_default(self):
        sample_filter = CurrentLapTimeFilter(self.system_channels)
        channel_data = {}
        sample_filter.filter(channel_data)
        self.assertEqual(None, channel_data.get(CurrentLapTimeFilter.CURRENT_LAPTIME_KEY))

    def test_laptime_last_laptime_only(self):
        sample_filter = CurrentLapTimeFilter(self.system_channels)
        channel_data = {CurrentLapTimeFilter.LAST_LAPTIME_KEY: 1.0}
        sample_filter.filter(channel_data)
        self.assertEqual(1.0, channel_data.get(CurrentLapTimeFilter.CURRENT_LAPTIME_KEY))

    def test_laptime_pred_only(self):
        sample_filter = CurrentLapTimeFilter(self.system_channels)
        channel_data = {CurrentLapTimeFilter.PREDICTED_LAPTIME_KEY: 1.0}
        sample_filter.filter(channel_data)
        self.assertEqual(1.0, channel_data.get(CurrentLapTimeFilter.PREDICTED_LAPTIME_KEY))

    def test_laptime_last_and_pred_time_present(self):
        sample_filter = CurrentLapTimeFilter(self.system_channels)
        channel_data = {CurrentLapTimeFilter.PREDICTED_LAPTIME_KEY:3.0,
                        CurrentLapTimeFilter.LAST_LAPTIME_KEY:1.0,
                        CurrentLapTimeFilter.CURRENT_LAPTIME_KEY:2.0}
        sample_filter.filter(channel_data)
        self.assertEqual(3.0, channel_data.get(CurrentLapTimeFilter.CURRENT_LAPTIME_KEY))
        