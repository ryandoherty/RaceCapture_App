
class SampleMetaException(Exception):
    pass

class ChannelMeta(object):
    name = None
    units = None
    min = 0
    max = 100
    precision = 0
    sampleRate = 0
    
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 0)
        self.units = kwargs.get('samples', self.units)
        self.min = kwargs.get('min', self.min)
        self.max = kwargs.get('max', self.max)
        self.precision = kwargs.get('prec', self.precision)
        self.sampleRate = kwargs.get('sampleRate', self.sampleRate)
        
    def fromJson(self, json):
        self.name = json.get('nm', self.name)
        self.units = json.get('ut', self.units)
        self.min = json.get('min', self.min)
        self.max = json.get('max', self.max)
        self.precision = json.get('prec', self.precision)
        self.sampleRate = int(json.get('sr', self.sampleRate))

class SampleValue(object):
    def __init__(self, value, channelMeta):
        self.value = value
        self.channelMeta = channelMeta

STARTING_BITMAP = 1
        
class Sample(object):
    tick = 0
    samples = []
    channelMetas = []
    updatedMeta = False
    
    def __init__(self, **kwargs):
        self.tick = kwargs.get('tick', self.tick)
        self.samples = kwargs.get('samples', self.samples)
        self.channelMetas = kwargs.get('channelMetas', self.channelMetas)
        self.updatedMeta = len(self.channelMetas) > 0
        
    def fromJson(self, json):
        if json:
            sample = json.get('s')
            if sample:
                self.tick = sample.get('t', 0)
                metaJson = sample.get('meta')
                dataJson = sample.get('d')
                if metaJson:
                    self.processMeta(metaJson)
                else:
                    self.updatedMeta = False
                if dataJson:
                    self.processData(dataJson)

    def processMeta(self, metaJson):
        channelMetas = self.channelMetas
        del channelMetas[:]
        for ch in metaJson:
            config = ChannelMeta()
            config.fromJson(ch)
            channelMetas.append(config)
        self.updatedMeta = True
    
    def processData(self, dataJson):
        
        channelConfigs = self.channelMetas
        channelConfigCount = len(channelConfigs)        
        bitmaskFieldCount = channelConfigCount / 32 + 1 if channelConfigCount % 32 > 0 else 0
        
        maxFieldCount = channelConfigCount + bitmaskFieldCount
                
        fieldData = dataJson
        fieldDataSize = len(fieldData)
        if fieldDataSize > maxFieldCount or fieldDataSize < bitmaskFieldCount:
            raise SampleMetaException('Unexpected data packet count {}; channel meta expects between {} and {} channels'.format(fieldDataSize, bitmaskFieldCount, maxFieldCount))

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
                sample = SampleValue(value, channelConfigs[channelConfigIndex])
                samples.append(sample)
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
