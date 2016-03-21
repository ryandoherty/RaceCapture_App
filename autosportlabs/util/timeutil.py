__all__ = ('time_to_epoch')
import calendar
from datetime import datetime

def time_to_epoch(timestamp):
    '''
    convert a timestamp to a Unix epoch
    :param timestamp in "YYYY-MM-DDTHH:MM:SSS" format
    :type string
    '''
    return int(calendar.timegm(datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").timetuple()))
