
'''Contains a references to a data source
'''
class SourceRef(object):
    lap = 0
    session = 0
    def __init__(self, lap, session):
        self.lap = lap
        self.session = session
   
    def __str__(self):
        return "{}_{}".format(self.lap, self.session)
    
'''Describes an event to synchronize views
'''     
class MarkerEvent(object):
    data_index = 0
    sourceref = None
    def __init__(self, data_index, sourceref):
        self.data_index = data_index
        self.sourceref = sourceref
        