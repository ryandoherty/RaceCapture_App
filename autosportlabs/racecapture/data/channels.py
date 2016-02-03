import json
import copy
import os
import traceback
from kivy.event import EventDispatcher
from collections import OrderedDict
from kivy.properties import ObjectProperty

CHANNEL_TYPE_UNKNOWN    = 0
CHANNEL_TYPE_SENSOR     = 1
CHANNEL_TYPE_IMU        = 2
CHANNEL_TYPE_GPS        = 3
CHANNEL_TYPE_TIME       = 4
CHANNEL_TYPE_STATS      = 5

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

UNKNOWN_CHANNEL = ChannelMeta(name='Unknown')

class RuntimeChannels(EventDispatcher):
    data_bus = ObjectProperty(None, allownone=True)
    system_channels = ObjectProperty(None, allownone=True)
    channels = OrderedDict()
    channel_names = []
        
    def __init__(self, **kwargs):
        super(RuntimeChannels, self).__init__(**kwargs)
        self.system_channels = kwargs['system_channels']
        self.reload_system_channels()
    
    def findChannelMeta(self, channel, default=UNKNOWN_CHANNEL):
        channelMeta = self.channels.get(channel)
        if not channelMeta: channelMeta = default
        return channelMeta
    
    def on_data_bus(self, instance, value):
        value.addMetaListener(self.on_runtime_channel_meta)
    
    def reload_system_channels(self):
        channels = self.channels
        channels.clear()
        #first, pull in the system channel defaults
        self.channel_names = list(self.system_channels.channel_names)
        for channel_name, system_meta in self.system_channels.channels.iteritems():
            channels[channel_name] = system_meta
        
    def on_runtime_channel_meta(self, runtime_channel_meta):
        #first, reload the default set of channels
        self.reload_system_channels()
        
        channels = self.channels
        #now override defaults with current runtime values
        for channel_name, runtime_meta in runtime_channel_meta.iteritems():
            existing_meta = channels.get(channel_name)
            
            if existing_meta is not None:
                #override existing channel meta with channel meta from runtime
                existing_meta.name = runtime_meta.name
                existing_meta.units = runtime_meta.units
                existing_meta.min = runtime_meta.min
                existing_meta.max = runtime_meta.max
                existing_meta.precision = runtime_meta.precision
            else:
                #this is a channel (possibly a custom channel) that isn't in the system defaults.
                #put it at the top of the list
                self.channel_names.insert(0,channel_name)
                channels[channel_name] = copy.copy(runtime_meta)

    def get_active_channels(self):
        '''
        Return a dict of active ChannelMeta objects. If we have a data connection, filter for only the currently active channels.
        If no data connection, send back all System channels
        :returns dict of ChannelMeta objects, keyed by channel name
        '''
        if self.data_bus.rcp_meta_read == True:
            return self.data_bus.channel_metas.copy()
        else:
            return self.channels.copy()

class SystemChannels(EventDispatcher):
    channels = ObjectProperty(None)
    channel_names = []
    unknownChannel = ChannelMeta(name='Unknown')
        
    def __init__(self, **kwargs):
        super(SystemChannels, self).__init__(**kwargs)        
        try:
            base_dir = kwargs.get('base_dir')
            base_dir = '.' if base_dir is None else base_dir
            system_channels_path = open(os.path.join(base_dir, 'resource', 'channel_meta', 'system_channels.json'))
            systemChannelsJson = json.load(system_channels_path)
            channelsJson = systemChannelsJson.get('channels')
            channels = OrderedDict()
            channel_names = []
            for channelJson in channelsJson:
                channel = ChannelMeta()
                channel.fromJson(channelJson) 
                channels[channel.name] = channel
                channel_names.append(channel.name)
            self.channels = channels
            self.channel_names = channel_names
        except Exception as detail:
            print('Error loading system channels: {}'.format(str(detail)))
            traceback.print_exc()

    def findChannelMeta(self, channel, default=UNKNOWN_CHANNEL):
        channelMeta = self.channels.get(channel)
        if not channelMeta: channelMeta = default
        return channelMeta

