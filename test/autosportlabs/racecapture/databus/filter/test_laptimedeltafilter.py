#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

import unittest
from autosportlabs.racecapture.databus.filter.laptimedeltafilter import LaptimeDeltaFilter
from autosportlabs.racecapture.data.channels import SystemChannels


class LaptimeDeltaFilterTest(unittest.TestCase):
    system_channels = SystemChannels()
    
    def test_laptime_delta_filter_meta(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        meta = sample_filter.get_channel_meta({'LapTime': {'foo': 'bar'}})
        self.assertTrue(LaptimeDeltaFilter.LAP_DELTA_KEY in meta)

    def test_laptime_delta_filter_skip(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        meta = sample_filter.get_channel_meta({})
        self.assertFalse(LaptimeDeltaFilter.LAP_DELTA_KEY in meta)

        channel_data = {}
        sample_filter.filter(channel_data)
        self.assertFalse(LaptimeDeltaFilter.LAP_DELTA_KEY in channel_data)

    def test_laptime_delta_only_laptime(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        channel_data = {LaptimeDeltaFilter.LAPTIME_KEY:1.0,
                        LaptimeDeltaFilter.BEST_LAPTIME_KEY:2.0}
        sample_filter.filter(channel_data)
        self.assertEqual(-60.0, channel_data.get(LaptimeDeltaFilter.LAP_DELTA_KEY))

    def test_laptime_delta_only_predtime(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        channel_data = {LaptimeDeltaFilter.PREDTIME_KEY:1.0,
                        LaptimeDeltaFilter.BEST_LAPTIME_KEY:2.0}
        sample_filter.filter(channel_data)
        self.assertEqual(-60.0, channel_data.get(LaptimeDeltaFilter.LAP_DELTA_KEY))

    def test_laptime_delta_predtime_and_laptime_present(self):
        sample_filter = LaptimeDeltaFilter(self.system_channels)
        channel_data = {LaptimeDeltaFilter.PREDTIME_KEY:3.0,
                        LaptimeDeltaFilter.LAPTIME_KEY:1.0,
                        LaptimeDeltaFilter.BEST_LAPTIME_KEY:2.0}
        sample_filter.filter(channel_data)
        self.assertEqual(60.0, channel_data.get(LaptimeDeltaFilter.LAP_DELTA_KEY))
