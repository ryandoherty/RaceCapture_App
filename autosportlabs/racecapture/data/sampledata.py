from autosportlabs.racecapture.data.channels import ChannelMeta, ChannelMetaCollection

class SampleMetaException(Exception):
    pass
        
class SampleValue(object):
    def __init__(self, value, channelMeta):
        self.value = value
        self.channelMeta = channelMeta

STARTING_BITMAP = 1
        
class Sample(object):
    tick = 0
    samples = []
    metas = ChannelMetaCollection()
    updated_meta = False
    
    def __init__(self, **kwargs):
        self.tick = kwargs.get('tick', self.tick)
        self.samples = kwargs.get('samples', self.samples)
        self.metas = kwargs.get('channelMetas', self.metas)
        self.updated_meta = len(self.metas.channel_metas) > 0
        
    def fromJson(self, json):
        if json:
            sample = json.get('s')
            if sample:
                self.tick = sample.get('t', 0)
                metaJson = sample.get('meta')
                dataJson = sample.get('d')
                if metaJson:
                    self.metas.fromJson(metaJson)
                    self.updated_meta = True
                else:
                    self.updated_meta = False
                if dataJson:
                    self.processData(dataJson)
    
    def processData(self, dataJson):
        metas = self.metas.channel_metas
        channelConfigCount = len(metas) 
        bitmaskFieldCount = max(0, (channelConfigCount - 1) / 32) + 1       
        
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
        
        channelConfigIndex = 0
        bitmapIndex = 0
        fieldIndex = 0
        mask_index = 0
        channelConfigCount = len(metas)
        while channelConfigIndex < channelConfigCount:
            if mask_index >= 32:            
                mask_index = 0;
                bitmapIndex += 1
                if bitmapIndex > len(bitmaskFields):
                    raise Exception("channel count overflowed number of bitmap fields available")
            
            mask = 1 << mask_index
            if (bitmaskFields[bitmapIndex] & mask) != 0:
                value = float(fieldData[fieldIndex])
                fieldIndex += 1
                sample = SampleValue(value, metas[channelConfigIndex])
                samples.append(sample)
            channelConfigIndex += 1
            mask_index += 1
