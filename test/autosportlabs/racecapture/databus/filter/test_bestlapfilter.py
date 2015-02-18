import unittest
from autosportlabs.racecapture.databus.filter.bestlapfilter import BestLapFilter
from autosportlabs.racecapture.data.sampledata import SystemChannels

class BestLapFilterTest(unittest.TestCase):
    system_channels = SystemChannels()
    
    def test_bestlap_meta(self):
        sample_filter = BestLapFilter(self.system_channels)
        meta = sample_filter.get_channel_meta()
        self.assertIsNotNone(meta.get(BestLapFilter.BEST_LAPTIME_KEY))
        
    def test_best_lap_default(self):
        sample_filter = BestLapFilter(self.system_channels)
        channel_data = {}
        
        sample_filter.filter(channel_data)
        self.assertIsNone(channel_data.get(BestLapFilter.BEST_LAPTIME_KEY))

    def test_first_best_lap(self):
        sample_filter = BestLapFilter(self.system_channels)
        channel_data = {'LapTime':111.111}
        
        sample_filter.filter(channel_data)
        self.assertEqual(111.111, channel_data.get(BestLapFilter.BEST_LAPTIME_KEY))

    def test_next_best_lap(self):
        sample_filter = BestLapFilter(self.system_channels)
        channel_data = {'LapTime':111.111}
        
        sample_filter.filter(channel_data)
        self.assertEqual(111.111, channel_data.get(BestLapFilter.BEST_LAPTIME_KEY))
        
        channel_data['LapTime'] = 110.111
        sample_filter.filter(channel_data)
        self.assertEqual(110.111, channel_data.get(BestLapFilter.BEST_LAPTIME_KEY))
        
    def test_best_lap_preserved(self):
        sample_filter = BestLapFilter(self.system_channels)
        channel_data = {'LapTime':111.111}
        
        sample_filter.filter(channel_data)
        self.assertEqual(111.111, channel_data.get(BestLapFilter.BEST_LAPTIME_KEY))
        
        channel_data['LapTime'] = 112.111
        sample_filter.filter(channel_data)
        self.assertEqual(111.111, channel_data.get(BestLapFilter.BEST_LAPTIME_KEY))
        