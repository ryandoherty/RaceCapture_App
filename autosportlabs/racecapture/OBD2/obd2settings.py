import os
import json

class OBD2Settings(object):
    obd2channelInfo = {}
    base_dir = None
    def __init__(self, base_dir=None, **kwargs):
        super(OBD2Settings, self).__init__(**kwargs)
        self.base_dir = base_dir
        self.loadOBD2Channels()
        
        
    def getPidForChannelName(self, name):
        pid = 0
        obd2Channel = self.obd2channelInfo.get(name)
        if obd2Channel:
            pid = int(obd2Channel['pid'])
        return pid
    
    def getChannelNames(self):
        return self.obd2channelInfo.keys()
    
    def loadOBD2Channels(self):
        try:
            obd2_json = open(os.path.join(self.base_dir, 'resource', 'settings', 'obd2_channels.json'))
            obd2channels = json.load(obd2_json)
            obd2channels = obd2channels['obd2Channels']
            
            for name in obd2channels:
                self.obd2channelInfo[name] = obd2channels[name]
        except Exception as detail:
            print('Error loading obd2 channel info ' + str(detail))
        