
class ChannelConfig(object):
    def __init__(self, **kwargs):
        self.name = None
        self.units = None
        self.sampleRate = 0
        
    def fromJson(self, json):
        self.name = json.get('nm', self.name)
        self.units = json.get('ut', self.units)
        self.sampleRate = int(json.get('sr', self.sampleRate))

class Sample(object):
    def __init__(self, value, channelConfig):
        self.value = value
        self.channelConfig = channelConfig

STARTING_BITMAP = 1
        
class SampleData(object):
    def __init__(self, **kwargs):
        self.tick = 0
        self.samples = []
        self.channelConfigs = []
        self.bitmask = 0

    def fromJson(self, json):
        if json:
            sample = json.get('s')
            if sample:
                self.tick = sample.get('t', 0)
                metaJson = sample.get('meta')
                dataJson = sample.get('d')
                if metaJson:
                    self.processMeta(metaJson)
                if dataJson:
                    self.processData(dataJson)

    def processMeta(self, metaJson):
        channelConfigs = self.channelConfigs
        del channelConfigs[:]
        for ch in metaJson:
            config = ChannelConfig()
            config.fromJson(ch)
            channelConfigs.append(config)
    
    def processData(self, dataJson):
        
        channelConfigs = self.channelConfigs
        channelConfigCount = len(channelConfigs)        
        bitmaskFieldCount = channelConfigCount / 32 + 1 if channelConfigCount % 32 > 0 else 0
        
        maxFieldCount = channelConfigCount + bitmaskFieldCount
                
        fieldData = dataJson
        fieldDataSize = len(fieldData)
        if fieldDataSize > maxFieldCount: raise Exception("Data packet count exceeds expected field count")
        if fieldDataSize < bitmaskFieldCount: raise Exception('Incorrect number of sample data fields detected')

        bitmaskFields = []
        for i in range(fieldDataSize - bitmaskFieldCount, fieldDataSize):
            bitmaskFields.append(int(fieldData[i]))
        
        samples = self.samples
        del samples[:]
        
        mask = STARTING_BITMAP
        
        channelConfigIndex = 0
        bitmapIndex = 0
        fieldIndex = 0
        channelConfigCount = len(channelConfigs)
        while channelConfigIndex < channelConfigCount:
            if (bitmaskFields[bitmapIndex] & mask) != 0:
                value = float(fieldData[fieldIndex])
                fieldIndex += 1
                samples.append(Sample(value, channelConfigs[channelConfigIndex]))

            if (mask != 0):
                mask <<= 1;
            else:
                mask = STARTING_BITMAP;
                bitmapIndex += 1
                if bitmapIndex > bitmaskFields.length:
                    raise Exception("channel count overflowed number of bitmap fields available")
            channelConfigIndex+=1

        
    def toJson(self):
        gpsJson = {'gpsCfg':{
                              'sr' : self.sampleRate,
                              'pos' : self.positionEnabled,
                              'speed' : self.speedEnabled,
                              'time' : self.timeEnabled,
                              'dist' : self.distanceEnabled,
                              'sats' : self.satellitesEnabled
                              }
                    }
                   
        return gpsJson
