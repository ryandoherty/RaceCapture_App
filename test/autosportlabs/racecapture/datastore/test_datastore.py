import unittest
import os, os.path
from autosportlabs.racecapture.datastore.datastore import DataStore, Filter, \
    DataSet

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
        dataset = self.ds.query(channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        expected_channels = ['Coolant', 'RPM', 'MAP']
        dset_channels = dataset.channels

        #Sort both lists to ensure that they'll compare properly
        expected_channels.sort()
        dset_channels.sort()

        self.assertListEqual(expected_channels, dset_channels)

    def test_dataset_val_count(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        samples = dataset.fetch_columns(100)

        for k in samples.keys():
            self.assertEqual(len(samples[k]), 100)

    def test_dataset_record_oriented(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        records = dataset.fetch_records(100)

        self.assertEqual(len(records), 100)

    def test_channel_min_max(self):
        rpm_min = self.ds.get_channel_min('RPM')
        rpm_max = self.ds.get_channel_max('RPM')

        self.assertEqual(rpm_min, 776.0)
        self.assertEqual(rpm_max, 6246.0)

    def test_channel_smoothing(self):
        success = None
        smoothing_rate = 0
        #positive case, this would appropriately set the smoothing
        
        self.ds.set_channel_smoothing('RPM', 100)

        smoothing_rate = self.ds.get_channel_smoothing('RPM')
        
        self.assertEqual(smoothing_rate, 100)

        #Negative case, this would return an error
        try:
            self.ds.set_channel_smoothing('AverageSpeedOfASwallow', 9001)
            success = True
        except:
            success = False

        self.assertEqual(success, False)
        
