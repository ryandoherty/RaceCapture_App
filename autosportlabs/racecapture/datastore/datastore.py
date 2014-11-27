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

class DataSet(object):
    def __init__(self, cursor):
        self._cur = cursor

    @property
    def channels(self):
        return [x[0] for x in self._cur.description]

    def fetch_columns(self, count, start=0):
        chanmap = {}
        channels = [x[0] for x in self._cur.description]

        dset = self._cur.fetchmany(count)

        for c in channels:
            idx = channels.index(c)
            chanmap[c] = [x[idx] for x in dset]

        return chanmap

    def fetch_records(self, count, start=0):
        chanmap = self.fetch_columns(count, start)

        #We have to pull the channel datapoint lists out in the order
        #that you'd expect to find them in the data cursor
        zlist = []
        for ch in self.channels:
            zlist.append(chanmap[ch])

        return zip(*zlist)

#Channel container classes
class intv(object):
    def __init__(self, chan):
        self.chan = chan

    def __str__(self):
        return self.chan


#Filter container class
#TODO: add a list of channels
class Filter(object):
    def __init__(self):
        self._cmd_seq = ''
        self._comb_op = 'AND '

    def add_combop(f):
        def wrap(self, *args, **kwargs):
            if len(self._cmd_seq):
                self._cmd_seq += self._comb_op
            ret = f(self, *args, **kwargs)
            return ret
        return wrap

    def chan_adj(f):
        def wrap(self, chan, val):
            prefix = 'datapoint_interp.' if 'intv' in type(chan).__name__ else 'datapoint_extrap.'
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
        self.channel_name = channel_name
        self.units = units
        self.sample_rate = sample_rate


class DataStore(object):
    val_filters = ['lt', 'gt', 'eq', 'lt_eq', 'gt_eq']
    def __init__(self, name=':memory:'):
        self._headers = []
        self._isopen = False
        self.datalog_channels = {}
        self.datalogchanneltypes = {}


    def close(self):
        self._conn.close()
        self._isopen = False

    def open_db(self, name):
        if self._isopen:
            self.close()

        self.name = name
        self._conn = sqlite3.connect(self.name)

        self._isopen = True

    def new(self, name=':memory:'):
        self.open_db(name)
        self._create_tables()

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

        self._conn.execute("""CREATE TABLE datapoint_extrap
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        datalog_id INTEGER NOT NULL,
        ts REAL NOT NULL) """)

        self._conn.execute("""CREATE TABLE datapoint_interp
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        datalog_id INTEGER NOT NULL,
        ts REAL NOT NULL)""")

        self._conn.execute("""CREATE TABLE datalog
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL)""")

        self._conn.execute("""CREATE INDEX datalog_index_id on datalog(id)""")

        self._conn.execute("""CREATE TABLE channel_types
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        units TEXT NOT NULL, smoothing INTEGER NOT NULL,
        min REAL NULL, max REAL NULL)""")

        self._conn.execute("""CREATE TABLE channels
        (id INTEGER PRIMARY KEY, name TEXT NOT NULL,
        type_id integer NOT NULL, description TEXT NULL)""")

        self._conn.execute("""CREATE TABLE datalog_channel_map
        (datalog_id INTEGER NOT NULL, channel_id INTEGER NOT NULL)""")

        self._conn.execute("""CREATE TABLE datalog_event_map
        (datalog_id INTEGER NOT NULL, event_id INTEGER NOT NULL)""")

        self._conn.commit()

    def _extend_datalog_channels(self, channel_names):
        #print "Adding channels: ", channel_names
        for channel_name in channel_names:
            self._conn.execute("""ALTER TABLE datapoint_extrap
            ADD {} REAL""".format(channel_name))
            self._conn.execute("""ALTER TABLE datapoint_interp
            ADD {} REAL""".format(channel_name))

        self._conn.commit()

    def _parse_datalog_headers(self, header):
        channels = header.split(',')
        headers = []

        try:
            new_channels = []
            for i in range(1, len(channels)+1):
                name, units, samplerate = channels[i -1].replace('"', '').split('|')
                #print name, units, samplerate
                header = DatalogChannel(name, units, int(samplerate), 0)
                headers.append(header)
                if not name in [x.channel_name for x in self._headers] and not name == 'ts':
                    new_channels.append(name)
                    self._headers.append(header)
            self._extend_datalog_channels(new_channels)
        except:
            raise Exception("Unable to import datalog, bad metadata")

        return headers

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

    def _insert_record(self, record, headers, session_id):
        """
        Takes a record of interpolated+extrapolated channels and their header metadata
        and inserts it into the database
        """
        datalog_id = self._get_last_table_id('datalog') + 1

        #First, insert into the datalog table to give us a reference
        #point for the datapoint insertions

        self._conn.execute("""INSERT INTO datalog
        (session_id) VALUES (?)""", [session_id])

        #TODO: do we need to do this to ensure the datalog ID will be valid?
        #self._conn.commit()

        #Insert the datapoints into their tables
        interp_vals = [datalog_id] + [x[0] for x in record]
        extrap_vals = [datalog_id] + [x[1] for x in record]

        #Now, insert the record into the datalog table using the ID
        #list we built up in the previous iteration

        for tbl in [('datapoint_interp', interp_vals), ('datapoint_extrap', extrap_vals)]:
            #Put together an insert statement containing the column names
            base_sql = "INSERT INTO {} (".format(tbl[0])
            base_sql += ','.join(['datalog_id'] + [x.channel_name for x in headers])
            base_sql += ') VALUES ('

            #insert the values
            base_sql += ','.join([str(x) for x in tbl[1]])
            base_sql += ')'

            #print "Executing SQL Statement: \n{}".format(base_sql)
            self._conn.execute(base_sql)


        #TODO: should this commit be at the end of inserting all of
        #the records instead?
        #self._conn.commit()

    def _interp_extrap_datapoints(self, datapoints):
        """
        Takes a list of datapoints, and returns a new list of interpolated+extrapolated datapoints

        i.e: '3, nil, nil, nil, 7' (as a column) will become:
        [(3, 3), (4, 3), (5, 3), (6, 3), (7, 7)]

         In the event of the 'start' of the dataset, we may have something like:
        [nil, nil, nil, 5], in this case, we will just back extrapolate, so:
        [nil, nil, nil, 5] becomes [(5, 5), (5, 5), (5, 5), (5, 5)]

        """

        ret_list = []

        # first we need to handle the 'start of dataset, begin on a
        # miss' case
        if datapoints[0] == None:
            ret_list = [(datapoints[-1], datapoints[-1]) for x in datapoints]
            return ret_list

        # Next, we need to handle the case where there are only two
        # entries and both are hits, if this is the case, we just
        # duplicate the values in the tuple for each entry and return
        # that
        if len(datapoints) == 2:
            ret_list = [(x, x) for x in datapoints]
            return ret_list

        # If we're here, it means we actually have a start and end
        # point to this data sample, have blanks in between and need
        # to interpolate+extrapolate the bits in between

        # Get the slope of the change so we can properly interpolate
        slope = _get_interp_slope(start = datapoints[0], finish = datapoints[-1], num_samples = len(datapoints))

        interp_list = []
        for p in range(len(datapoints)):
            interp_val = datapoints[0] + (p * slope)
            interp_list.append(interp_val)

        extrap_list = []
        for e in range(len(datapoints) - 1):
            extrap_list.append(datapoints[0])
        extrap_list.append(datapoints[-1])

        ret_list = zip(interp_list, extrap_list)
        return ret_list


    def _desparsified_data_generator(self, data_file):
        """
        Takes a racecapture pro CSV file and removes sparsity from the dataset.
        This function yields samples that have been interpolated/extrapolated from the
        parent dataset.  These samples will come in the form of a list of tuples in the form
        (interpolated, extrapolated)

        'interpolated' means that given [3, nil, nil, nil, 7] in a column, you will receive: [3, 4, 5, 6, 7]
        'extrapolated' means that we'll just carry all values forward: [3, nil, nil, nil, 7] -> [3, 3, 3, 3, 7, 7, 7...]

        So to summarize: '3, nil, nil, nil, 7' (as a column) will become:
        [(3, 3), (4, 3), (5, 3), (6, 3), (7, 7)]

        In the event of the 'start' of the dataset, we may have something like:
        [nil, nil, nil, 5], in this case, we will just back extrapolate, so:
        [nil, nil, nil, 5] becomes [(5, 5), (5, 5), (5, 5), (5, 5)]
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
        # columnar list [0:hit], interpolate and extrapolate the
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
                    mod_list = self._interp_extrap_datapoints(work_list[c])

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
                ds_to_yield = [x[0] for x in yield_list]
                map(lambda x: x.pop(0), yield_list)
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

    def _handle_data(self, data_file, headers, session_id):
        """
        takes a raw dataset in the form of a CSV file and inserts the data
        into the sqlite database
        """

        #Create the generator for the desparsified data
        newdata_gen = self._desparsified_data_generator(data_file)

        for record in newdata_gen:
            self._insert_record(record, headers, session_id)
            #print record

        self._conn.commit()


    @timing
    def import_datalog(self, path, name, notes='', progress_listener=None):
        try:
            dl = open(path, 'rb')
        except:
            raise Exception("Unable to open file")

        header = dl.readline()

        headers = self._parse_datalog_headers(header)

        #Create an event to be tagged to these records
        ses_id = self._create_session(name, notes)

        self._handle_data(dl, headers, ses_id)

    def query(self, channels=[], data_filter=None):
        #Build our select statement
        sel_st  = 'SELECT '

        columns = []
        joins = []

        #If there are no channels, or if a '*' is passed, select all
        #of the channels
        if len(channels) == 0 or '*' in channels:
            channels = [x.chan_name for x in self._headers]

        for ch in channels:
            #TODO: Make sure we have a record of this channel
            chanst = str(ch)
            tbl_prefix = 'datapoint_interp.' if 'intv' in type(ch).__name__ else 'datapoint_extrap.'
            alias = ' as {}'.format(chanst)
            columns.append(tbl_prefix+chanst+alias)
            joins.append(tbl_prefix+chanst)

        #Add the columns to the select statement
        sel_st += ','.join(columns)

        #Point out where we're pulling this from
        sel_st += '\nFROM datalog\n'

        #Add our joins
        datapoint_tables = ['datapoint_interp', 'datapoint_extrap']
        for tbl in datapoint_tables:
            sel_st += 'JOIN {} ON {}.datalog_id=datalog.id\n'.format(tbl, tbl)

        #Add our filter
        sel_st += 'WHERE '

        if not data_filter == None:
            if not 'Filter' in type(data_filter).__name__:
                raise TypeError("data_filter must be of class Filter")

            sel_st += str(data_filter)

        c = self._conn.cursor()
        c.execute(sel_st)
        return DataSet(c)
