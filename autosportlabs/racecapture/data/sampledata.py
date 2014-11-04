import json
from collections import OrderedDict
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty

CHANNEL_TYPE_UNKNOWN    = 0
CHANNEL_TYPE_ANALOG     = 1
CHANNEL_TYPE_FREQ       = 2
CHANNEL_TYPE_GPIO       = 3
CHANNEL_TYPE_PWM        = 4
CHANNEL_TYPE_IMU        = 5
CHANNEL_TYPE_GPS        = 6
CHANNEL_TYPE_STATISTICS = 7

class SampleMetaException(Exception):
    pass

class ChannelMeta(object):
    name = None
    units = None
    min = 0
    max = 100
    precision = 0
    sampleRate = 0
    type = 0
    
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.units = kwargs.get('units', self.units)
        self.min = kwargs.get('min', self.min)
        self.max = kwargs.get('max', self.max)
        self.precision = kwargs.get('prec', self.precision)
        self.sampleRate = kwargs.get('sampleRate', self.sampleRate)
        self.type = kwargs.get('type', self.type)
        
    def fromJson(self, json):
        self.name = json.get('nm', self.name)
        self.units = json.get('ut', self.units)
        self.min = json.get('min', self.min)
        self.max = json.get('max', self.max)
        self.precision = json.get('prec', self.precision)
        self.sampleRate = int(json.get('sr', self.sampleRate))
        self.type = int(json.get('type', self.type))

class ChannelMetaCollection(object):
    channel_metas = []
    
    def fromJson(self, metaJson):
        channel_metas = self.channel_metas
        del channel_metas[:]
        for ch in metaJson:
            channel_meta = ChannelMeta()
            channel_meta.fromJson(ch)
            channel_metas.append(channel_meta)
        
class SystemChannels(EventDispatcher):
    channels = ObjectProperty(None)
    unknownChannel = ChannelMeta(name='Unknown')
        
    def __init__(self, **kwargs):
        try:
            systemChannelsJson = json.load(open('resource/channel_meta/system_channels.json'))
            channelsJson = systemChannelsJson.get('channels')
            channels = OrderedDict()
            for channelJson in channelsJson:
                channel = ChannelMeta()
                channel.fromJson(channelJson) 
                channels[channel.name] = channel
            self.channels = channels
            
        except Exception as detail:
            print('Error loading system channels: {}'.format(str(detail)))

    def findChannelMeta(self, channel):
        channelMeta = self.channels.get(channel)
        if not channelMeta: channelMeta = self.unknownChannel
        return channelMeta

class SampleValue(object):
    def __init__(self, value, channelMeta):
        self.value = value
        self.channelMeta = channelMeta

STARTING_BITMAP = 1
        
class Sample(object):
    tick = 0
    samples = []
    channel_metas = ChannelMetaCollection()
    updated_meta = False
    
    def __init__(self, **kwargs):
        self.tick = kwargs.get('tick', self.tick)
        self.samples = kwargs.get('samples', self.samples)
        self.channel_metas = kwargs.get('channelMetas', self.channel_metas)
        self.updated_meta = len(self.channel_metas) > 0
        
    def fromJson(self, json):
        if json:
            sample = json.get('s')
            if sample:
                self.tick = sample.get('t', 0)
                metaJson = sample.get('meta')
                dataJson = sample.get('d')
                if metaJson:
                    self.channel_meta.fromJson(metaJson)
                    self.updated_meta = True
                else:
                    self.updated_meta = False
                if dataJson:
                    self.processData(dataJson)
    
    def processData(self, dataJson):
        
        channelConfigs = self.channel_metas
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
