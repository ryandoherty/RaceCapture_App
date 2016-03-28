#!/usr/bin/python
import sqlite3
import logging
import os, os.path
import time
import datetime
from kivy.logger import Logger

class DatastoreException(Exception):
    pass

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
        Logger.info('Datastore: {} function took {} ms'.format(f.func_name, (time2-time1)*1000.0))
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
        raise DatastoreException("Invalid smoothing rate")

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

    def fetch_columns(self, count=None):
        chanmap = {}
        channels = [x[0] for x in self._cur.description]

        if count == None:
            dset = self._cur.fetchall()
        else:
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

    def fetch_records(self, count=None):
        chanmap = self.fetch_columns(count)

        #We have to pull the channel datapoint lists out in the order
        #that you'd expect to find them in the data cursor
        zlist = []
        for ch in self.channels:
            zlist.append(chanmap[ch])

        return zip(*zlist)

class Session(object):
    def __init__(self, session_id, name, notes = '', date = None):
        self.session_id = session_id
        self.name = name
        self.notes = notes
        self.date = date
        
class Lap(object):
    def __init__(self, lap, session_id, lap_time):
        self.lap = lap
        self.session_id = session_id
        self.lap_time = lap_time

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
    def neq(self, chan, val):
        self._cmd_seq += '{} != {} '.format(chan, val)
        return self

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
    def __init__(self, channel_name='', units='', min=0, max=0, sample_rate=0, smoothing=0):
        self.name = channel_name
        self.units = units
        self.min = min
        self.max = max
        self.sample_rate = sample_rate

    def __str__(self):
        return self.name

class DataStore(object):
    EXTRA_INDEX_CHANNELS = ["CurrentLap"]    
    val_filters = ['lt', 'gt', 'eq', 'lt_eq', 'gt_eq']
    def __init__(self):
        self._channels = []
        self._isopen = False
        self.datalog_channels = {}
        self.datalogchanneltypes = {}
        self._new_db = False
        self._ending_datalog_id  = 0
        

    def close(self):
        self._conn.close()
        self._isopen = False

    @property
    def db_path(self):
        return self._db_path[:]

    def open_db(self, db_path):
        if self._isopen:
            self.close()

        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)

        if not self._new_db:
            self._populate_channel_list()

        self._isopen = True

    def new(self, db_path=':memory:'):
        self._new_db = True
        self.open_db(db_path)
        self._create_tables()

    def _populate_channel_list(self):
        c = self._conn.cursor()

        self._channels = []
        c.execute("""SELECT name, units, min_value, max_value, smoothing
        from channel""")

        for ch in c.fetchall():
            self._channels.append(DatalogChannel(channel_name=ch[0],
                                                 units=ch[1],
                                                 min=ch[2],
                                                 max=ch[3],
                                                 smoothing=ch[4]))

    @property
    def is_open(self):
        return self._isopen

    @property
    def channel_list(self):
        return self._channels[:]

    def get_channel(self, name):
        '''
        Retreives information for a channel
        :param name the channel name
        :type name string
        :returns DatalogChannel object for the channel. Raises DatastoreException if channel is unknown
        ''' 
        channel =  [c for c in self._channels if name in c.name]
        if not len(channel):
            raise DatastoreException("Unknown channel: {}".format(name))
        return channel[0]
        
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
        
        self._conn.execute("""CREATE INDEX datapoint_sample_id_index_id on datapoint(sample_id)""")

        self._conn.execute("""CREATE TABLE sample
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL)""")
        self._conn.execute("""CREATE INDEX sample_id_index_id on sample(id)""")
        self._conn.execute("""CREATE INDEX sample_session_id_index_id on sample(session_id)""")

        self._conn.execute("""CREATE TABLE channel
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        units TEXT NOT NULL, min_value REAL NOT NULL, max_value REAL NOT NULL,
         smoothing INTEGER NOT NULL)""")

        self._conn.execute("""CREATE TABLE datalog_channel_map
        (datalog_id INTEGER NOT NULL, channel_id INTEGER NOT NULL)""")

        self._conn.execute("""CREATE TABLE datalog_event_map
        (datalog_id INTEGER NOT NULL, event_id INTEGER NOT NULL)""")

        self._conn.commit()

    
    def _add_extra_indexes(self, channels):
        extra_indexes = []
        for c in channels:
            c = str(c)
            if c in self.EXTRA_INDEX_CHANNELS:
                extra_indexes.append(c)
        
        for index_channel in extra_indexes:
            self._conn.execute("""CREATE INDEX {}_index_id on datapoint({})""".format(index_channel, index_channel))
        
    def _extend_datalog_channels(self, channels):
        for channel in channels:
            #Extend the datapoint table to include the channel as a
            #new field
            self._conn.execute("""ALTER TABLE datapoint
            ADD {} REAL""".format(channel.name))

            #Add the channel to the 'channel' table
            self._conn.execute("""INSERT INTO channel (name, units, min_value, max_value, smoothing)
            VALUES (?,?,?,?,?)""", (channel.name, channel.units, channel.min, channel.max, 1))

        self._add_extra_indexes(channels)
        self._conn.commit()

    def _parse_datalog_headers(self, header):
        raw_channels = header.split(',')
        channels = []

        try:
            new_channels = []
            for i in range(1, len(raw_channels)+1):
                name, units, min, max, samplerate = raw_channels[i -1].replace('"', '').split('|')
                channel = DatalogChannel(name, units, float(min), float(max), int(samplerate), 0)
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
            raise DatastoreException("Unable to import datalog, bad metadata")

        return channels

    def _get_last_table_id(self, table_name):
        """
        Returns the last used ID number (as an int) from the specified table name

        This is useful when inserting new data as we use this number to join on the datalog table
        """

        c = self._conn.cursor()
        base_sql = "SELECT * FROM SQLITE_SEQUENCE WHERE name='{}';".format(table_name)
        c.execute(base_sql)
        res = c.fetchone()

        if res == None:
            dl_id = 0
        else:
            dl_id = res[1] # comes back as sample|<last id>
        return dl_id

    def insert_record(self, record, channels, session_id):
        """
        Takes a record of interpolated+extrapolated channels and their header metadata
        and inserts it into the database
        """

        cursor = self._conn.cursor()
        try:
            #First, insert into the datalog table to give us a reference
            #point for the datapoint insertions
            cursor.execute("""INSERT INTO sample (session_id) VALUES (?)""", [session_id])
            datalog_id = cursor.lastrowid
    
            #Insert the datapoints into their tables
            extrap_vals = [datalog_id] + record
    
            #Now, insert the record into the datalog table using the ID
            #list we built up in the previous iteration
    
            #Put together an insert statement containing the column names
            base_sql = "INSERT INTO datapoint ({}) VALUES({});".format(','.join(['sample_id'] + [x.name for x in channels]), 
                                                                       ','.join([str(x) for x in extrap_vals]))
            cursor.execute(base_sql)
            self._conn.commit()
        except: #rollback under any exception, then re-raise exception
            self._conn.rollback()
            raise

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


    def _desparsified_data_generator(self, data_file, warnings=None, progress_cb=None):
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
            work_list_len = len(work_list)
            channels_len = len(channels)
            if work_list_len == 0:
                work_list = [[] for x in channels]
                yield_list = [[] for x in channels]
            
            if channels_len > work_list_len and current_line > 0:
                warn_msg = 'Unexpected channel count in line {}. Expected {}, got {}'.format(current_line, work_list_len, channels_len)
                if warnings:
                    warnings.append((line, warn_msg))
                Logger.warn("DataStore: {}".format(warn_msg))
                continue

            # Down to business, first, we stuff each channel's sample
            # into the work list
            for c in range(channels_len):
                work_list[c].append(channels[c])

            # At this point, we need to walk through each channel
            # column in the work list.  If the length of the column is
            # 1, we simply move onto the next column.  If the length
            # is > 1, we check if column[-1] is a miss (None) or a
            # hit(anything else).  If it is a hit, we
            # interpolate/extrapolate the column, then move everything
            # EXCEPT the last item into the yield list

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

        #now, finish off and extrapolate the remaining items in the
        #work list and extend the yield list with the resultant values
        for idx in range(len(work_list)):
            set_len = len(work_list[idx])
            work_list[idx] = [work_list[idx][0] for x in range(set_len)]
            yield_list[idx].extend(work_list[idx])

        #Yield off the remaining items in the yield list
        while not 0 in [len(x) for x in yield_list]:
            current_line += 1
            ds_to_yield = [x[0] for x in yield_list]
            map(lambda x: x.pop(0), yield_list)
            if progress_cb:
                percent_complete = float(current_line) / line_count * 100
                progress_cb(percent_complete)
            yield ds_to_yield

    def delete_session(self, session_id):
        self._conn.execute("""DELETE FROM datapoint WHERE sample_id in (select id from sample where session_id = ?)""", (session_id,))
        self._conn.execute("""DELETE FROM sample WHERE session_id=?""",(session_id,))
        self._conn.execute("""DELETE FROM session where id=?""",(session_id,))
        self._conn.commit()
        
    def _create_session(self, name, notes=''):
        """
        Creates a new session entry in the sessions table and returns it's ID
        """

        current_time = unix_time(datetime.datetime.now())
        self._conn.execute("""INSERT INTO session
        (name, notes, date)
        VALUES (?, ?, ?)""", (name, notes, current_time))

        self._conn.commit()
        session_id = self._get_last_table_id('session')

        Logger.info('DataStore: Created session with ID: {}'.format(session_id))
        return session_id


    #class member variable to track ending datalog id when importing
    def _handle_data(self, data_file, headers, session_id, warnings=None, progress_cb=None):
        """
        takes a raw dataset in the form of a CSV file and inserts the data
        into the sqlite database.
        
        This function is not thread-safe.
        """

        starting_datalog_id = self._get_last_table_id('sample') + 1
        self._ending_datalog_id = starting_datalog_id

        def sample_iter(count, sample_id):
            for x in range(count):
                yield [sample_id]
            
        def datapoint_iter(data, datalog_id):
            for record in data:
                record = [datalog_id] + record
                datalog_id += 1
                yield record
            self._ending_datalog_id = datalog_id
            
        #Create the generator for the desparsified data
        newdata_gen = self._desparsified_data_generator(data_file, warnings=warnings, progress_cb=progress_cb)

        #Put together an insert statement containing the column names
        datapoint_sql = "INSERT INTO datapoint ({}) VALUES ({});".format(','.join(['sample_id'] + [x.name for x in headers]), 
                                                                         ','.join(['?'] * (len(headers) + 1)))

        #Relatively static insert statement for sample table
        sample_sql = "INSERT INTO sample (session_id) VALUES (?)"
        
        #Use a generator to efficiently insert data into table, within a transaction
        cur = self._conn.cursor()
        try:
            cur.executemany(datapoint_sql, datapoint_iter(newdata_gen, starting_datalog_id))
            cur.executemany(sample_sql, sample_iter(self._ending_datalog_id - starting_datalog_id, session_id))
            self._conn.commit()
        except: #rollback under any exception, then re-raise exception
            self._conn.rollback()
            raise

    def get_location_center(self, sessions=None):
        c = self._conn.cursor()

        base_sql = 'SELECT AVG(Latitude), AVG(Longitude) from datapoint'
        
        if type(sessions) == list and len(sessions) > 0:
            base_sql += ' JOIN sample ON datapoint.sample_id=sample.id WHERE sample.session_id IN({}) AND datapoint.Latitude != 0 AND datapoint.Longitude != 0;'.format(','.join(map(str, sessions)))

        c.execute(base_sql)
        res = c.fetchone()
        
        lat_average = None
        lon_average = None
        if res:
            lat_average =  res[0]
            lon_average =  res[1]
        return (lat_average, lon_average)
                
    def _session_select_clause(self, sessions=None):
        sql = ''
        if type(sessions) == list and len(sessions) > 0:
            sql += ' JOIN sample ON datapoint.sample_id=sample.id WHERE sample.session_id IN({})'.format(','.join(map(str, sessions)))            
        return sql
        
    def get_channel_average(self, channel, sessions=None):
        c = self._conn.cursor()

        base_sql = "SELECT AVG({}) from datapoint {};".format(channel, self._session_select_clause(sessions))
        c.execute(base_sql)
        res = c.fetchone()
        average = None if res == None else res[0]
        return average
        
    def _extra_channels(self, extra_channels=None):
        sql = ''
        if type(extra_channels) == list:
            for channel in extra_channels:
                sql += ',{}'.format(channel)
        return sql

    def _get_channel_aggregate(self, aggregate, channel, sessions=None, extra_channels=None, exclude_zero=True):
        c = self._conn.cursor()

        base_sql = "SELECT {}({}) {} from datapoint {} {};".format(aggregate, channel,
                                                                 self._extra_channels(extra_channels),
                                                                 self._session_select_clause(sessions),
                                                                 '{} {} > 0'.format('AND' if sessions else 'WHERE', channel) if exclude_zero else '')
        c.execute(base_sql)
        res = c.fetchone()
        return None if res == None else res if extra_channels else res[0]
                
    def get_channel_max(self, channel, sessions=None, extra_channels=None):
        return self._get_channel_aggregate('MAX', channel, sessions=sessions, extra_channels=extra_channels)

    def get_channel_min(self, channel, sessions=None, extra_channels=None, exclude_zero=True):
        return self._get_channel_aggregate('MIN', channel, sessions=sessions, extra_channels=extra_channels)

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
            raise DatastoreException("Unknown channel: {}".format(channel))

        self._conn.execute("""UPDATE channel
        SET smoothing={}
        WHERE name='{}'
        """.format(smoothing, channel))

    def get_channel_smoothing(self, channel):
        if not channel in [x.name for x in self._channels]:
            raise DatastoreException("Unknown channel: {}".format(channel))

        c = self._conn.cursor()

        base_sql = "SELECT smoothing from channel WHERE channel.name='{}';".format(channel)
        c.execute(base_sql)

        res = c.fetchone()

        if res == None:
            raise DatastoreException("Unable to retrieve smoothing for channel: {}".format(channel))
        else:
            return res[0]

    @timing
    def import_datalog(self, path, name, notes='', progress_cb=None):
        warnings = []
        if not self._isopen:
            raise DatastoreException("Datastore is not open")
        try:
            dl = open(path, 'rb')
        except:
            raise DatastoreException("Unable to open file")

        header = dl.readline()
        headers = self._parse_datalog_headers(header)

        #Create an event to be tagged to these records
        session_id = self._create_session(name, notes)
        self._handle_data(dl, headers, session_id, warnings, progress_cb)
        
        #update the channel metadata, including re-setting min/max values
        self.update_channel_metadata()
        return session_id

    def query(self, sessions=[], channels=[], data_filter=None, distinct_records=False):
        #Build our select statement
        sel_st  = 'SELECT '

        if distinct_records:
            sel_st += 'DISTINCT '

        columns = []
        joins = []

        #make sure that the sessions list exists
        if type(sessions) != list or len(sessions) == 0:
            raise DatastoreException("Must provide a list of sessions to query!")

        #If there are no channels, or if a '*' is passed, select all
        #of the channels
        if len(channels) == 0 or '*' in channels:
            channels = [x.chan_name for x in self._channels]

        for ch in channels:
            if not ch in [x.name for x in self._channels]:
                raise DatastoreException("Unable to complete query. Unknown channel: {}".format(ch))
            chanst = str(ch)
            tbl_prefix = 'datapoint.'
            alias = ' as {}'.format(chanst)
            columns.append(tbl_prefix+chanst+alias)
            joins.append(tbl_prefix+chanst)

        #Make the session ID the first column
        ses_sel = "sample.session_id as session_id"
        columns.insert(0, ses_sel)

        #Add the columns to the select statement
        sel_st += ','.join(columns)

        #Point out where we're pulling this from
        sel_st += '\nFROM sample\n'

        #Add our joins
        sel_st += 'JOIN datapoint ON datapoint.sample_id=sample.id\n'

        if data_filter is not None:
            #Add our filter
            sel_st += 'WHERE '
            if not 'Filter' in type(data_filter).__name__:
                raise TypeError("data_filter must be of class Filter")

            sel_st += str(data_filter)

        #create the session filter
        if data_filter == None:
            ses_st = "WHERE "
        else:
            ses_st = "AND "
            
        ses_filters = []
        for s in sessions:
            ses_filters.append('sample.session_id = {}'.format(s))

        ses_st += 'OR '.join(ses_filters)

        #Now add the session filter to the select statement
        sel_st += ses_st

        Logger.debug('[datastore] Query execute: {}'.format(sel_st))
        c = self._conn.cursor()
        c.execute(sel_st)

        smoothing_map = {}
        #Put together the smoothing map
        for ch in channels:
            sr = self.get_channel_smoothing(ch)
            smoothing_map[ch] = sr

        #add the session_id to the smoothing map with a smoothing rate
        #of 0
        smoothing_map['session_id'] = 0
        
        return DataSet(c, smoothing_map)
    
    def get_session_by_id(self, session_id, sessions=None):
        sessions = self.get_sessions() if not sessions else sessions
        session = next((x for x in sessions if x.session_id == session_id), None)
        return session
        
    def get_sessions(self):
        c = self._conn.cursor()

        sessions = []
        for row in c.execute('SELECT id, name, notes, date FROM session ORDER BY name COLLATE NOCASE ASC;'):
            sessions.append(Session(session_id=row[0], name=row[1], notes=row[2], date=row[3]))
        
        return sessions

    def get_laps(self, session_id):
        '''
        Fetches a list of lap information for the specified session id
        :param session_id the session id
        :type session_id int
        :returns list of Lap objects
        :type list 
        '''        
        laps = []
        c = self._conn.cursor()
        for row in c.execute('''SELECT DISTINCT sample.session_id AS session_id, 
                                datapoint.CurrentLap AS CurrentLap, 
                                max(datapoint.ElapsedTime) AS ElapsedTime
                                FROM sample
                                JOIN datapoint ON datapoint.sample_id=sample.id
                                WHERE datapoint.CurrentLap > 0
                                AND sample.session_id = ?
                                GROUP BY CurrentLap, session_id
                                ORDER BY datapoint.CurrentLap ASC;''',
                                (session_id,)):
            laps.append(Lap(session_id=row[0], lap=row[1], lap_time=row[2]))
        return laps
                
        
    def update_session(self, session):
        self._conn.execute("""UPDATE session SET name=?, notes=?, date=? WHERE id=?;""", (session.name, session.notes, unix_time(datetime.datetime.now()), session.session_id ,))
        self._conn.commit()
        
    def update_channel_metadata(self, channels=None, only_extend_minmax=True):
        '''
        Adjust the channel min/max values as necessary based on the min/max values present in the datapoints
        :param channels list of channels to update. If None, all channels are updated
        :type channels list
        :param only_extend_minmax True if min/max values should only be extended. If false, min/max are adjusted to actual min/max values in datapoint
        :type only_extend_minmax bool 
        '''
        cursor = self._conn.cursor()
        channels_to_update = [x for x in self._channels if channels is None or x.name in channels]
        for channel in channels_to_update:
            name = channel.name
            min_max = cursor.execute('SELECT COALESCE(MIN({}), 0), COALESCE(MAX({}), 0) FROM datapoint;'.format(name, name))
            record = min_max.fetchone()
            datapoint_min_value = record[0]
            datapoint_max_value = record[1]
            min_value = channel.min if only_extend_minmax == True else datapoint_min_value
            max_value = channel.max if only_extend_minmax == True else datapoint_max_value
            if only_extend_minmax == True:
                selected_min_value = min(min_value, datapoint_min_value)
                selected_max_value = max(max_value, datapoint_max_value) 
            else:
                selected_min_value = datapoint_min_value
                selected_max_value = datapoint_max_value

            Logger.info('Datastore: updating min/max for {}'.format(name))
            sql = 'UPDATE channel SET min_value={}, max_value={} WHERE name="{}";'.format(selected_min_value, 
                                                                                          selected_max_value, 
                                                                                          name) 
            cursor.execute(sql)
        self._conn.commit()
        self._populate_channel_list()
