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

    @classmethod
    def tearDownClass(self):
        self.ds.close()
        os.remove(db_path)

    def test_aaa_valid_import(self):
        #HACK
        # Note the strange name here: I need to be sure that this runs
        # first as other tests will rely on the fact that there is
        # actually data in the database.  Since this can take several
        # seconds to populate, I don't want to waste everyone's time
        try:
            self.ds.import_datalog(log_path, 'rc_adj')
            success = True
        except:
            import sys, traceback
            print "Exception in user code:"
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60

            success = False

        self.assertEqual(success, True)

    def test_basic_filter(self):
        f = Filter().lt('LapCount', 1)

        expected_output = 'datapoint.LapCount < 1'
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

    def test_channel_min_max(self):
        rpm_min = self.ds.get_channel_min('RPM')
        rpm_max = self.ds.get_channel_max('RPM')

        self.assertEqual(rpm_min, 498.0)
        self.assertEqual(rpm_max, 6246.0)

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
        print len(records)

        self.assertEqual(len(records), 25691)
        
