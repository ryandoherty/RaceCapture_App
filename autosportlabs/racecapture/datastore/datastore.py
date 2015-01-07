#!/usr/bin/python
import sqlite3
import logging
import os, os.path
import time
import datetime

def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return unix_time(dt) * 1000.0

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f ms' % (f.func_name, (time2-time1)*1000.0)
        return ret
    return wrap

def _get_interp_slope(start, finish, num_samples):
    #print "Start, finish, num_samples", start, finish, num_samples
    if start == finish:
        return 0

    return float(start - finish) / float(1 - num_samples)

def _interp_dpoints(start, finish, sample_skip):
    slope = _get_interp_slope(start, finish, sample_skip + 1)

    nlist = [start]
    for i in range(sample_skip - 1):
        nlist.append(float(nlist[-1] + slope))

    nlist.append(finish)

    return nlist

def _smooth_dataset(dset, smoothing_rate):
    #Throw an error if we got a bad smoothing rate
    if not smoothing_rate or smoothing_rate < 2:
        raise Exception("Invalid smoothing rate")

    #This is the dataset that we'll be returning
    new_dset = []

    #Get every nth sample from the dataset where n==smoothing_rate
    dpoints = dset[0::smoothing_rate]

    #Now, loop through the target datapoints, interpolate the values
    #between, and store them to the new dataset that we'll be
    #returning
    for index, val in enumerate(dpoints[:-1]):
        #Get the start and end points of the interpolation
        start = val
        end = dpoints[index+1]

        #Generate the smoothed dataset
        smoothed_samples = _interp_dpoints(start, end, smoothing_rate)

        #Append everything but the last datapoint in the smoothed
        #samples to the new dataset
        #(This will be the first item in the next dataset)
        new_dset.extend(smoothed_samples[:-1])

        #If the end was the last datapoint in the original set, append
        #it as well
        if index + 1 == len(dpoints) - 1:
            new_dset.append(end)

    #Now we need to smooth out the tail end of the list (if necessary)
    if len(new_dset) < len(dset):
        #calculate the difference in lengths between the original and
        #new datasets
        len_diff = len(dset) - len(new_dset)

        #generate a new smoothed dataset for the missing elements
        tail_dset = _interp_dpoints(new_dset[-1], dset[-1], len_diff)

        #Extend our return list with everything but the tail of the
        #new_dataset (as this would cause a duplicate)
        new_dset.extend(tail_dset[1:])

    return new_dset

class DataSet(object):
    def __init__(self, cursor, smoothing_map=None):
        self._cur = cursor
        self._smoothing_map = smoothing_map

    @property
    def channels(self):
        return [x[0] for x in self._cur.description]

    #TODO: Do we want to offer a count of None to do a fetch all?
    def fetch_columns(self, count):
        chanmap = {}
        channels = [x[0] for x in self._cur.description]

        dset = self._cur.fetchmany(count)
        for c in channels:
            idx = channels.index(c)
            chan_dataset =  [x[idx] for x in dset]

            #If we received a smoothing map and the smoothing rate of
            #the selected channel is > 1, smooth it out before
            #returning it to the user
            if self._smoothing_map and self._smoothing_map[c] > 1:
                chan_dataset = _smooth_dataset(chan_dataset, self._smoothing_map[c])
            chanmap[c] = chan_dataset

        return chanmap

    def fetch_records(self, count):
        chanmap = self.fetch_columns(count)

        #We have to pull the channel datapoint lists out in the order
        #that you'd expect to find them in the data cursor
        zlist = []
        for ch in self.channels:
            zlist.append(chanmap[ch])

        return zip(*zlist)


#Filter container class
class Filter(object):
    def __init__(self):
        self._cmd_seq = ''
        self._comb_op = 'AND '
        self._channels = []

    @property
    def channels(self):
        return self._channels[:]

    def add_combop(f):
        def wrap(self, *args, **kwargs):
            if len(self._cmd_seq):
                self._cmd_seq += self._comb_op
            ret = f(self, *args, **kwargs)
            return ret
        return wrap

    def chan_adj(f):
        def wrap(self, chan, val):
            self._channels.append(chan)
            prefix = 'datapoint.'
            chan = prefix+str(chan)
            ret = f(self, chan, val)
            return ret
        return wrap

    @add_combop
    @chan_adj
    def eq(self, chan, val):
        self._cmd_seq += '{} = {} '.format(chan, val)
        return self

    @add_combop
    @chan_adj
    def lt(self, chan, val):
        self._cmd_seq += '{} < {} '.format(chan, val)
        return self

    @add_combop
    @chan_adj
    def gt(self, chan, val):
        self._cmd_seq += '{} > {} '.format(chan, val)
        return self

    @add_combop
    @chan_adj
    def lteq(self, chan, val):
        self._cmd_seq += '{} <= {} '.format(chan, val)
        return self

    @add_combop
    @chan_adj
    def gteq(self, chan, val):
        self._cmd_seq += '{} >= {} '.format(chan, val)
        return self

    def and_(self):
        self._comb_op = 'AND '
        return self

    def or_(self):
        self._comb_op = 'OR '
        return self

    def __str__(self):
        return self._cmd_seq
        return self

    @add_combop
    def group(self, filterchain):
        self._cmd_seq += '({})'.format(str(filterchain).strip())
        return self


class DatalogChannel(object):
    def __init__(self, channel_name='', units='', sample_rate=0, smoothing=0):
        self.name = channel_name
        self.units = units
        self.sample_rate = sample_rate


class DataStore(object):
    val_filters = ['lt', 'gt', 'eq', 'lt_eq', 'gt_eq']
    def __init__(self):
        self._channels = []
        self._isopen = False
        self.datalog_channels = {}
        self.datalogchanneltypes = {}
        self._new_db = False

    def close(self):
        self._conn.close()
        self._isopen = False

    def open_db(self, name):
        if self._isopen:
            self.close()

        self.name = name
        self._conn = sqlite3.connect(self.name, check_same_thread=False)

        if not self._new_db:
            self._populate_channel_list()

        self._isopen = True

    def new(self, name=':memory:'):
        self._new_db = True
        self.open_db(name)
        self._create_tables()

    def _populate_channel_list(self):
        c = self._conn.cursor()

        c.execute("""SELECT name, units, smoothing
        from channel""")

        for ch in c.fetchall():
            self._channels.append(DatalogChannel(channel_name=ch[0],
                                                 units=ch[1],
                                                 smoothing=ch[2]))

    @property
    def is_open(self):
        return self._isopen

    @property
    def channel_list(self):
        return self._channels[:]

    def _create_tables(self):

        self._conn.execute("""CREATE TABLE session
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        notes TEXT NULL,
        date INTEGER NOT NULL)""")

        self._conn.execute("""CREATE TABLE datalog_info
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        max_sample_rate INTEGER NOT NULL, time_offset INTEGER NOT NULL,
        name TEXT NOT NULL, notes TEXT NULL)""")

        self._conn.execute("""CREATE TABLE datapoint
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id INTEGER NOT NULL)""")

        self._conn.execute("""CREATE TABLE sample
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL)""")

        self._conn.execute("""CREATE INDEX sample_index_id on sample(id)""")

        self._conn.execute("""CREATE TABLE channel
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        units TEXT NOT NULL, smoothing INTEGER NOT NULL)""")

        self._conn.execute("""CREATE TABLE datalog_channel_map
        (datalog_id INTEGER NOT NULL, channel_id INTEGER NOT NULL)""")

        self._conn.execute("""CREATE TABLE datalog_event_map
        (datalog_id INTEGER NOT NULL, event_id INTEGER NOT NULL)""")

        self._conn.commit()

    def _extend_datalog_channels(self, channels):
        #print "Adding channels: ", channel_names
        for channel in channels:
            #Extend the datapoint table to include the channel as a
            #new field
            self._conn.execute("""ALTER TABLE datapoint
            ADD {} REAL""".format(channel.name))

            #Add the channel to the 'channel' table
            self._conn.execute("""INSERT INTO channel (name, units, smoothing)
            VALUES (?,?,?)""", (channel.name, channel.units, 1))

        self._conn.commit()

    def _parse_datalog_headers(self, header):
        raw_channels = header.split(',')
        channels = []

        try:
            new_channels = []
            for i in range(1, len(raw_channels)+1):
                name, units, samplerate = raw_channels[i -1].replace('"', '').split('|')
                #print name, units, samplerate
                channel = DatalogChannel(name, units, int(samplerate), 0)
                channels.append(channel)
                if not name in [x.name for x in self._channels]:
                    new_channels.append(channel)
                    self._channels.append(channel)
            self._extend_datalog_channels(new_channels)
        except:
            import sys, traceback
            print "Exception in user code:"
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            raise Exception("Unable to import datalog, bad metadata")

        return channels

    def _get_last_table_id(self, table_name):
        """
        Returns the last used ID number (as an int) from the specified table name

        This is useful when inserting new data as we use this number to join on the datalog table
        """

        c = self._conn.cursor()
        base_sql = "SELECT id from {} ORDER BY id DESC LIMIT 1;".format(table_name)
        c.execute(base_sql)

        res = c.fetchone()

        if res == None:
            dl_id = 0
        else:
            dl_id = res[0]
        #print "Last datapoint ID =", dp_id
        return dl_id

    def _insert_record(self, record, channels, session_id):
        """
        Takes a record of interpolated+extrapolated channels and their header metadata
        and inserts it into the database
        """
        datalog_id = self._get_last_table_id('sample') + 1

        #First, insert into the datalog table to give us a reference
        #point for the datapoint insertions

        self._conn.execute("""INSERT INTO sample
        (session_id) VALUES (?)""", [session_id])

        #Insert the datapoints into their tables
        extrap_vals = [datalog_id] + record

        #Now, insert the record into the datalog table using the ID
        #list we built up in the previous iteration

        #Put together an insert statement containing the column names
        base_sql = "INSERT INTO datapoint ("
        base_sql += ','.join(['sample_id'] + [x.name for x in channels])
        base_sql += ') VALUES ('

        #insert the values
        base_sql += ','.join([str(x) for x in extrap_vals])
        base_sql += ')'

        #print "Executing SQL Statement: \n{}".format(base_sql)
        self._conn.execute(base_sql)

    def _extrap_datapoints(self, datapoints):
        """
        Takes a list of datapoints, and returns a new list of extrapolated datapoints

        i.e: '3, nil, nil, nil, 7' (as a column) will become:
        [3, 3, 3, 3, 7]

         In the event of the 'start' of the dataset, we may have something like:
        [nil, nil, nil, 5], in this case, we will just back extrapolate, so:
        [nil, nil, nil, 5] becomes [5, 5, 5, 5]

        """

        ret_list = []

        # first we need to handle the 'start of dataset, begin on a
        # miss' case
        if datapoints[0] == None:
            ret_list = [datapoints[-1] for x in datapoints]
            return ret_list

        # Next, we need to handle the case where there are only two
        # entries and both are hits, if this is the case, we just
        # duplicate the values in the tuple for each entry and return
        # that
        if len(datapoints) == 2:
            ret_list = [x for x in datapoints]
            return ret_list

        # If we're here, it means we actually have a start and end
        # point to this data sample, have blanks in between and need
        # to interpolate+extrapolate the bits in between

        extrap_list = []
        for e in range(len(datapoints) - 1):
            extrap_list.append(datapoints[0])
        extrap_list.append(datapoints[-1])

        return extrap_list


    def _desparsified_data_generator(self, data_file, progress_cb=None):
        """
        Takes a racecapture pro CSV file and removes sparsity from the dataset.
        This function yields samples that have been extrapolated from the
        parent dataset.

        'extrapolated' means that we'll just carry all values forward: [3, nil, nil, nil, 7] -> [3, 3, 3, 3, 7, 7, 7...]

        So to summarize: '3, nil, nil, nil, 7' (as a column) will become:
        [3, 3, 3, 3, 7]

        In the event of the 'start' of the dataset, we may have something like:
        [nil, nil, nil, 5], in this case, we will just back extrapolate, so:
        [nil, nil, nil, 5] becomes [5, 5, 5, 5]
        """

        # Notes on this algorithm: The basic idea is that we're going
        # 100% bob barker on this data...Think Plinko.
        # We maintain 2 lists of n lists where n = the number
        # of columns we're playing with.
        # Container list 1 holds our work space, we file records into
        # it one by one into their respective columnar lists.
        # A data point containing a NIL is a 'miss', a data point
        # containing some value is a 'hit'.  We continue to file until
        # we get a 'hit'.  When that happens, we take the slice of the
        # columnar list [0:hit], extrapolate the
        # values in between, then take the slice [0:hit-1] and insert
        # it into the second container list (in the same respective
        # column).  We shift container list 1's respective columnar
        # list by [hit:], then continue on.  We do this for EACH
        # columnar list in container list 1. (In the event that we're
        # just starting out and have misses at the head of the column,
        # instead of interpolating/extrapolating between hits, we just
        # back-extrapolate and shift as expected)
        # After this operation, we shift our attention to container
        # list 2.  If there is data in each column (i.e. len(col) > 0
        # for each column), we yield a new list containing:
        # [col0[0], col1[0], col2[0],...,coln[0]] and shift each
        # column down by 1 (i.e.: [1, 2, 3] becomes [2, 3])
        # That's right, this is a generator.  Booya.

        work_list = []
        yield_list = []

        #In order to facilitate a progress callback, we need to know
        #the number of lines in the file

        #Get the current file cursor position
        start_pos = data_file.tell()

        #Count the remaining lines in the file
        line_count = sum(1 for line in data_file)
        current_line = 0

        #Reset the file cursor
        data_file.seek(start_pos)
        
        for line in data_file:

            # Strip the line and break it down into it's component
            # channels, replace all blank entries with None
            channels = [None if x == '' else float(x) for x in line.strip().split(',')]
            #print channels

            # Now, if this is the first entry (characterized by
            # work_list being an empty list), we need to create all of
            # our 'plinko slots' for each channel in both the work and
            # yield lists
            if len(work_list) == 0:
                work_list = [[] for x in channels]
                yield_list = [[] for x in channels]

            # Down to business, first, we stuff each channel's sample
            # into the work list
            for c in range(len(channels)):
                work_list[c].append(channels[c])

            # At this point, we need to walk through each channel
            # column in the work list.  If the length of the column is
            # 1, we simply move onto the next column.  If the length
            # is > 1, we check if column[-1] is a miss (None) or a
            # hit(anything else).  If it is a hit, we
            # interpolate/extrapolate the column, then move everything
            # EXCEPT the last item into the yield list

            # TODO: See about moving this part into the above loop to
            # reduce algorithmic complexity
            for c in range(len(work_list)):
                if len(work_list[c]) == 1:
                    continue

                # If we have a hit at the end of the list, get the
                # extraploated/interpolated list of datapoints
                if not work_list[c][-1] == None:
                    mod_list = self._extrap_datapoints(work_list[c])

                    #Now copy everything but the last point in the
                    #modified list into the yield_list
                    yield_list[c].extend(mod_list[:-1])

                    #And remove everything BUT the last datapoint from
                    #the current list in work_list
                    work_list[c] = work_list[c][-1:]


            # Ok, we now have THINGS in our yield list, if we have
            # something in EVERY column of the yield list, create a
            # new list containing the first item in every column,
            # shift all columns down one, and yield the new list
            if not 0 in [len(x) for x in yield_list]:
                current_line += 1
                ds_to_yield = [x[0] for x in yield_list]
                map(lambda x: x.pop(0), yield_list)
                if progress_cb:
                    percent_complete = float(current_line) / line_count * 100
                    progress_cb(percent_complete)
                yield ds_to_yield

        #TODO: Finish off by extrapolating out the rest of the columns
        #and yielding them

    def _create_session(self, name, notes=''):
        """
        Creates a new session entry in the sessions table and returns it's ID
        """

        current_time = unix_time(datetime.datetime.now())
        self._conn.execute("""INSERT INTO session
        (name, notes, date)
        VALUES (?, ?, ?)""", (name, notes, current_time))

        self._conn.commit()
        ses_id = self._get_last_table_id('session')

        print "Created session with ID: ", ses_id
        return ses_id

    def _handle_data(self, data_file, headers, session_id, progress_cb=None):
        """
        takes a raw dataset in the form of a CSV file and inserts the data
        into the sqlite database
        """

        #Create the generator for the desparsified data
        newdata_gen = self._desparsified_data_generator(data_file, progress_cb)

        for record in newdata_gen:
            self._insert_record(record, headers, session_id)
            #print record

        self._conn.commit()

    def get_channel_max(self, channel):
        c = self._conn.cursor()

        base_sql = "SELECT {} from datapoint ORDER BY {} DESC LIMIT 1;".format(channel, channel)
        c.execute(base_sql)

        res = c.fetchone()

        if res == None:
            chan_max = None
        else:
            chan_max = res[0]
        return chan_max

    def get_channel_min(self, channel):
        c = self._conn.cursor()

        base_sql = "SELECT {} from datapoint ORDER BY {} ASC LIMIT 1;".format(channel, channel)
        c.execute(base_sql)

        res = c.fetchone()

        if res == None:
            chan_min = None
        else:
            chan_min = res[0]
        return chan_min

    def set_channel_smoothing(self, channel, smoothing):
        """
        Sets the smoothing rate on a per channel basis, this will be reflected in the returned dataset

        The 'smoothing' rate details how many samples we should skip and smooth out in the middle of a dataset, i.e:
        [1, 1, 1, 1, 5] with a smoothing rate of '4', would mean we evaluate this list as:
         0* 1  2  3  4*
        [1, x, x, x, 5], which would then be interpolated as:
        [1, 2, 3, 4, 5]
        """
        if smoothing < 1:
            smoothing = 1

        if not channel in [x.name for x in self._channels]:
            raise Exception("Unknown channel: {}".format(channel))

        self._conn.execute("""UPDATE channel
        SET smoothing={}
        WHERE name='{}'
        """.format(smoothing, channel))

    def get_channel_smoothing(self, channel):
        if not channel in [x.name for x in self._channels]:
            raise Exception("Unknown channel: {}".format(channel))

        c = self._conn.cursor()

        base_sql = "SELECT smoothing from channel WHERE channel.name='{}';".format(channel)
        c.execute(base_sql)

        res = c.fetchone()

        if res == None:
            raise Exception("Unable to retrieve smoothing for channel: {}".format(channel))
        else:
            return res[0]

    @timing
    def import_datalog(self, path, name, notes='', progress_cb=None):
        if not self._isopen:
            raise Exception("Datastore is not open")

        try:
            dl = open(path, 'rb')
        except:
            raise Exception("Unable to open file")

        header = dl.readline()

        headers = self._parse_datalog_headers(header)

        #Create an event to be tagged to these records
        ses_id = self._create_session(name, notes)

        self._handle_data(dl, headers, ses_id, progress_cb)

    def query(self, channels=[], data_filter=None):
        #Build our select statement
        sel_st  = 'SELECT '

        columns = []
        joins = []

        #If there are no channels, or if a '*' is passed, select all
        #of the channels
        if len(channels) == 0 or '*' in channels:
            channels = [x.chan_name for x in self._channels]

        for ch in channels:
            if not ch in [x.name for x in self._channels]:
                raise Exception("Unable to complete query. Unknown channel: {}".format(ch))
            chanst = str(ch)
            tbl_prefix = 'datapoint.'
            alias = ' as {}'.format(chanst)
            columns.append(tbl_prefix+chanst+alias)
            joins.append(tbl_prefix+chanst)

        #Add the columns to the select statement
        sel_st += ','.join(columns)

        #Point out where we're pulling this from
        sel_st += '\nFROM sample\n'

        #Add our joins
        sel_st += 'JOIN datapoint ON datapoint.sample_id=sample.id\n'

        #Add our filter
        sel_st += 'WHERE '

        if not data_filter == None:
            if not 'Filter' in type(data_filter).__name__:
                raise TypeError("data_filter must be of class Filter")

            sel_st += str(data_filter)

        c = self._conn.cursor()
        c.execute(sel_st)

        smoothing_map = {}
        #Put together the smoothing map
        for ch in channels:
            sr = self.get_channel_smoothing(ch)
            smoothing_map[ch] = sr
        
        return DataSet(c, smoothing_map)
