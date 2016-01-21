import unittest
import os, os.path
from autosportlabs.racecapture.datastore.datastore import DataStore, Filter, \
    DataSet, _interp_dpoints, _smooth_dataset

fqp = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(fqp, 'rctest.sql3')
log_path = os.path.join(fqp, 'rc_adj.log')

#NOTE! that
class DataStoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ds = DataStore()

        if os.path.exists(db_path):
            os.remove(db_path)

        self.ds.new(db_path)
        self._import_initial_data()

    @classmethod
    def tearDownClass(self):
        self._delete_all_sessions()
        self.ds.close()
        os.remove(db_path)

    @classmethod
    def _import_initial_data(self):
        try:
            self.ds.import_datalog(log_path, 'rc_adj', 'the notes')
        except:
            import sys, traceback
            print "Exception importing datalog:"
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60

    @classmethod
    def _delete_all_sessions(self):
        sessions = self.ds.get_sessions()
        for session in sessions:
            self.ds.delete_session(session.session_id)

    def test_delete_session(self):
        session_id = self.ds.import_datalog(log_path, 'rc_adj', 'the notes')
        self.ds.delete_session(session_id)
        session = self.ds.get_session_by_id(session_id)
        self.assertIsNone(session)

    def test_basic_filter(self):
        f = Filter().lt('LapCount', 1)

        expected_output = 'datapoint.LapCount < 1'
        filter_text = str(f).strip()

        self.assertSequenceEqual(filter_text, expected_output)

    def test_not_equal_filter(self):
        f = Filter().neq('LapCount', 1)
        
        expected_output = 'datapoint.LapCount != 1'
        filter_text = str(f).strip()
        
        self.assertSequenceEqual(filter_text, expected_output)
        
    def test_chained_filter(self):
        f = Filter().lt('LapCount', 1).gt('Coolant', 212).or_().eq('RPM', 9001)

        expected_output = 'datapoint.LapCount < 1 AND datapoint.Coolant > 212 OR datapoint.RPM = 9001'
        filter_text = str(f).strip()

        self.assertSequenceEqual(filter_text, expected_output)

    def test_grouped_filter(self):
        f = Filter().lt('LapCount', 1).group(Filter().gt('Coolant', 212).or_().gt('RPM', 9000))

        expected_output = 'datapoint.LapCount < 1 AND (datapoint.Coolant > 212 OR datapoint.RPM > 9000)'
        filter_text = str(f).strip()

        self.assertSequenceEqual(filter_text, expected_output)

    def test_dataset_columns(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        expected_channels = ['Coolant', 'RPM', 'MAP', 'session_id']
        dset_channels = dataset.channels

        #Sort both lists to ensure that they'll compare properly
        expected_channels.sort()
        dset_channels.sort()

        self.assertListEqual(expected_channels, dset_channels)

    def test_dataset_val_count(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        samples = dataset.fetch_columns(100)

        for k in samples.keys():
            self.assertEqual(len(samples[k]), 100)

    def test_dataset_record_oriented(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        records = dataset.fetch_records(100)

        self.assertEqual(len(records), 100)

    def test_channel_average(self):
        lat_avg = self.ds.get_channel_average("Latitude")
        lon_avg = self.ds.get_channel_average("Longitude")
        self.assertEqual(round(lat_avg, 6), 47.256164)
        self.assertEqual(round(lon_avg, 6), -123.191297)
         
    def test_channel_average_by_session(self):
        #session exists
        lat_avg = self.ds.get_channel_average("Latitude", sessions=[1])
        lon_avg = self.ds.get_channel_average("Longitude", sessions=[1])
        self.assertEqual(47.256164, round(lat_avg, 6))
        self.assertEqual(-123.191297, round(lon_avg, 6))
        
        #session does not exist
        lat_avg = self.ds.get_channel_average("Latitude", sessions=[2])
        lon_avg = self.ds.get_channel_average("Longitude", sessions=[2])
        self.assertEqual(None, lat_avg)
        self.assertEqual(None, lon_avg)

        #include an existing and not existing session
        lat_avg = self.ds.get_channel_average("Latitude", sessions=[1,2])
        lon_avg = self.ds.get_channel_average("Longitude", sessions=[1,2])
        self.assertEqual(47.256164, round(lat_avg, 6))
        self.assertEqual(-123.191297, round(lon_avg, 6))
        
    def test_channel_min_max(self):
        rpm_min = self.ds.get_channel_min('RPM')
        rpm_max = self.ds.get_channel_max('RPM')

        self.assertEqual(rpm_min, 498.0)
        self.assertEqual(rpm_max, 6246.0)
        
        #with extra channels
        rpm_min = self.ds.get_channel_min('RPM', extra_channels=['LapCount'])
        rpm_max = self.ds.get_channel_max('RPM', extra_channels=['LapCount'])

        self.assertEqual(rpm_min[0], 498.0)
        self.assertEqual(rpm_max[0], 6246.0)
        self.assertEqual(rpm_min[1], 37)
        self.assertEqual(rpm_max[1], 12)
        

    def test_interpolation(self):
        dset = [1., 1., 1., 1., 5.]

        smooth_list = _interp_dpoints(1, 5, 4)

        self.assertListEqual(smooth_list, [1., 2., 3., 4., 5.])


    def test_smoothing_even_bound(self):
        dset = [1., 1., 1., 1., 5.]
        smooth_list = _smooth_dataset(dset, 4)

        self.assertListEqual(smooth_list, [1., 2., 3., 4., 5.])

    def test_smoothing_offset_bound(self):
        dset = [1., 1., 1., 1., 5., 5., 5., 2]
        smooth_list = _smooth_dataset(dset, 4)

        self.assertListEqual(smooth_list, [1., 2., 3., 4., 5., 4., 3., 2.])


    def test_channel_set_get_smoothing(self):
        success = None
        smoothing_rate = 0
        #positive case, this would appropriately set the smoothing

        self.ds.set_channel_smoothing('RPM', 10)

        smoothing_rate = self.ds.get_channel_smoothing('RPM')

        self.assertEqual(smoothing_rate, 10)

        #reset the smoothing rate so we don't interfere with other tests
        self.ds.set_channel_smoothing('RPM', 1)

        smoothing_rate = self.ds.get_channel_smoothing('RPM')
        self.assertEqual(smoothing_rate, 1)
        

        #Negative case, this would return an error
        try:
            self.ds.set_channel_smoothing('AverageSpeedOfASwallow', 9001)
            success = True
        except:
            success = False

        self.assertEqual(success, False)

    def test_distinct_queries(self):
        """
        This is a really basic test to ensure that we always obey the distinct keyword

        Distinct should filter out duplicate results, leading to a much smaller dataset
        """

        f = Filter().gt('LapCount', 0)
        dataset = self.ds.query(sessions=[1],
                                channels=['LapCount', 'LapTime'],
                                data_filter=f)

        records = dataset.fetch_records()
        self.assertEqual(len(records), 24667)

        dataset = self.ds.query(sessions=[1],
                                channels=['LapCount', 'LapTime'],
                                data_filter=f,
                                distinct_records=True)

        records = dataset.fetch_records()
        self.assertEqual(len(records), 37)

    def test_no_filter(self):
        """
        This test ensures that we can query the entire datastore without a filter
        """

        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'])

        records = dataset.fetch_records()
        self.assertEqual(len(records), 25691)
        
    def test_get_all_laptimes(self):
        
        f = Filter().gt('LapCount', 0)
        dataset = self.ds.query(sessions=[1],
                                channels=['LapCount', 'LapTime'],
                                data_filter=f,
                                distinct_records=True)

        laptimes = {}
        records = dataset.fetch_records()
        for r in records:
            laptimes[int(r[1])] = r[2]

        self.assertEqual(laptimes[1],3.437)
        self.assertEqual(laptimes[2],2.257)
        self.assertEqual(laptimes[3],2.227)
        self.assertEqual(laptimes[4],2.313)
        self.assertEqual(laptimes[5],2.227)
        self.assertEqual(laptimes[6],2.227)
        self.assertEqual(laptimes[7],2.423)
        self.assertEqual(laptimes[8],2.31)
        self.assertEqual(laptimes[9],2.223)
        self.assertEqual(laptimes[10],2.233)
        self.assertEqual(laptimes[11],2.247)
        self.assertEqual(laptimes[12],2.24)
        self.assertEqual(laptimes[13],2.25)
        self.assertEqual(laptimes[14],2.237)
        self.assertEqual(laptimes[15],2.243)
        self.assertEqual(laptimes[16],2.29)
        self.assertEqual(laptimes[17],2.387)
        self.assertEqual(laptimes[18],2.297)
        self.assertEqual(laptimes[19],2.383)
        self.assertEqual(laptimes[20],2.177)
        self.assertEqual(laptimes[21],2.207)
        self.assertEqual(laptimes[22],2.18)
        self.assertEqual(laptimes[23],2.17)
        self.assertEqual(laptimes[24],2.22)
        self.assertEqual(laptimes[25],2.217)
        self.assertEqual(laptimes[26],2.223)
        self.assertEqual(laptimes[27],2.173)
        self.assertEqual(laptimes[28],2.19)
        self.assertEqual(laptimes[29],2.33)
        self.assertEqual(laptimes[30],2.227)
        self.assertEqual(laptimes[31],2.257)
        self.assertEqual(laptimes[32],2.183)
        self.assertEqual(laptimes[33],2.163)
        self.assertEqual(laptimes[34],2.23)
        self.assertEqual(laptimes[35],2.23)
        self.assertEqual(laptimes[36],2.54)
        self.assertEqual(laptimes[37],3.383)

    def test_get_sessions(self):
        sessions = self.ds.get_sessions()
        self.assertEqual(len(sessions), 1)
        session = sessions[0]
        self.assertEqual(session.name, 'rc_adj')
        self.assertEqual(session.session_id, 1)
        self.assertEqual(session.notes, 'the notes')
        self.assertIsNotNone(session.date)
        
    def test_location_center(self):
        lat, lon = self.ds.get_location_center([1])
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)
        
    def test_update_session(self):
        session = self.ds.get_sessions()[0]
        session.name='name_updated'
        session.notes='notes_updated'
        self.ds.update_session(session)
        session = self.ds.get_sessions()[0]
        self.assertEqual('name_updated', session.name)
        self.assertEqual('notes_updated', session.notes)
        
    def test_update_metadata(self):

        def get_channel(name):
            channels = self.ds.channel_list
            return [x for x in channels if x.name == name][0]
        
        #test update specific name
        accel_x = get_channel('AccelX')

        #simulate bad metadata for min/max
        accel_x.min = 0
        accel_x.max = 0
        self.ds.update_channel_metadata()
        accel_x = get_channel('AccelX')
        #AccelX min value should've been updated since the data file contains data < 0
        self.assertLess(accel_x.min, 0)
        self.assertGreater(accel_x.max, 0)
        
        #change min/max to an exceedingly large value
        #setting only_extend_minmax to false will force min/max to rail to actual min/max values in datapoint table
        accel_x.min = -100
        accel_x.max = 100
        self.ds.update_channel_metadata(only_extend_minmax=False)
        accel_x = get_channel('AccelX')
        #now it should be adjusted to be exactly the min value in the datapoints
        self.assertLess(-100, accel_x.min)
        self.assertGreater(100, accel_x.max)
        
        #Now test only updating specific channels
        #test update specific name
        accel_x = get_channel('AccelX')
        accel_y = get_channel('AccelY')
        
        #simulate bad metadata for min/max
        accel_x.min = 0
        accel_x.max = 0
        self.ds.update_channel_metadata(channels=['AccelX'], only_extend_minmax=False)
        new_accel_x = get_channel('AccelX')
        new_accel_y = get_channel('AccelY')
        
        #only AccelX should've been updated
        self.assertLess(new_accel_x.min, 0)
        self.assertGreater(new_accel_x.max, 0)
        #AccelY shoudn't have changed
        self.assertEqual(new_accel_y.min, accel_y.min)
        self.assertEqual(new_accel_y.max, accel_y.max)
