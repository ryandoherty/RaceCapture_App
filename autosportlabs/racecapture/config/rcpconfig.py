import json
from copy import copy
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from kivy.logger import Logger

RCP_COMPATIBLE_MAJOR_VERSION = 2
RCP_MINIMUM_MINOR_VERSION = 8

class BaseChannel(object):
    def __init__(self, **kwargs):
        self.name = 'Unknown'
        self.units = ''
        self.min = -1000
        self.max = 1000
        self.precision = 0
        self.sampleRate = 0
        self.stale = False
        
    def fromJson(self, json_dict):
        self.name = json_dict.get('nm', self.name) 
        self.units = json_dict.get('ut', self.units)
        self.min = json_dict.get('min', self.min)
        self.max = json_dict.get('max', self.max)
        self.precision = json_dict.get('prec', self.precision)
        self.sampleRate = json_dict.get('sr', self.sampleRate)
    
    def appendJson(self, json_dict):
        json_dict['nm'] = self.name
        json_dict['ut'] = self.units
        json_dict['min'] = self.min
        json_dict['max'] = self.max
        json_dict['prec'] = self.precision
        json_dict['sr'] = self.sampleRate        

SCALING_MAP_POINTS = 5
SCALING_MAP_MIN_VOLTS = 0

class ScalingMapException(Exception):
    pass

class ScalingMap(object):
    def __init__(self, **kwargs):
        points = SCALING_MAP_POINTS
        raw = []
        scaled = []
        for i in range(points):
            raw.append(0)
            scaled.append(0)
        self.points = points
        self.raw = raw
        self.scaled = scaled
 
    def fromJson(self, mapJson):
        rawJson = mapJson.get('raw', None)
        if rawJson:
            i = 0
            for rawValue in rawJson:
                self.raw[i] = rawValue
                i+=1

        scaledJson = mapJson.get('scal', None)
        if scaledJson:
            i = 0
            for scaledValue in scaledJson:
                self.scaled[i] = scaledValue
                i+=1
                
    def toJson(self):
        mapJson = {}
        rawBins = []
        scaledBins = []
        for rawValue in self.raw:
            rawBins.append(rawValue)
        
        for scaledValue in self.scaled:
            scaledBins.append(scaledValue)
            
        mapJson['raw'] = rawBins
        mapJson['scal'] = scaledBins
        
        return mapJson 
        
    def getVolts(self, mapBin):
        return self.raw[mapBin]
     
    def setVolts(self, map_bin, value):
        try:
            value = float(value)
        except:
            raise ScalingMapException("Value must be numeric")
        if map_bin < SCALING_MAP_POINTS - 1:
            next_value = self.raw[map_bin+1]
            if value > next_value:
                raise ScalingMapException("Must be less or equal to {}".format(next_value))
        if map_bin > 0:
            prev_value = self.raw[map_bin - 1]
            if value < prev_value:
                raise ScalingMapException("Must be greater or equal to {}".format(prev_value))
        if value < SCALING_MAP_MIN_VOLTS:
            raise ScalingMapException('Must be greater than {}'.format(SCALING_MAP_MIN_VOLTS))
        
        self.raw[map_bin] = value
            
    def getScaled(self, mapBin):
        try:
            return self.scaled[mapBin]
        except IndexError:
            Logger.error('ScalingMap: Index error getting scaled value')
            return 0
    
    def setScaled(self, mapBin, value):
        try:
            self.scaled[mapBin] = float(value)
        except IndexError:
            Logger.error('ScalingMap: Index error setting bin')
            
ANALOG_SCALING_MODE_RAW     = 0
ANALOG_SCALING_MODE_LINEAR  = 1
ANALOG_SCALING_MODE_MAP     = 2

class AnalogChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(AnalogChannel, self).__init__(**kwargs)        
        self.scalingMode = 0
        self.linearScaling = 0
        self.linearOffset = 0
        self.alpha = 0
        self.scalingMap = ScalingMap()
    
    def fromJson(self, json_dict):
        if json_dict:
            super(AnalogChannel, self).fromJson(json_dict)
            self.scalingMode = json_dict.get('scalMod', self.scalingMode)
            self.linearScaling = json_dict.get('scaling', self.linearScaling)
            self.linearOffset = json_dict.get('offset', self.linearOffset)
            self.alpha = json_dict.get('alpha', self.alpha)
            scaling_map_json = json_dict.get('map', None)
            if scaling_map_json:
                self.scalingMap.fromJson(scaling_map_json)
            self.stale = False
        
    def toJson(self):
        json_dict = {}
        super(AnalogChannel, self).appendJson(json_dict)
        json_dict['scalMod'] = self.scalingMode
        json_dict['scaling'] = self.linearScaling
        json_dict['offset'] = self.linearOffset
        json_dict['alpha'] = self.alpha
        json_dict['map'] = self.scalingMap.toJson()
        return json_dict
    
ANALOG_CHANNEL_COUNT = 8

class AnalogConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = ANALOG_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(AnalogChannel())   

    def fromJson(self, analogCfgJson):
        for i in range (self.channelCount):
            analogChannelJson = analogCfgJson.get(str(i), None)
            if analogChannelJson:
                self.channels[i].fromJson(analogChannelJson)

    def toJson(self):
        analogCfgJson = {}
        for i in range(ANALOG_CHANNEL_COUNT):
            analogChannel = self.channels[i]
            analogCfgJson[str(i)] = analogChannel.toJson()
        return {'analogCfg':analogCfgJson}
            
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value    
    
class ImuChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(ImuChannel, self).__init__(**kwargs)
        self.mode = 0
        self.chan = 0
        self.zeroValue = 0
        self.alpha = 0
        
    def fromJson(self, json_dict):
        if json_dict:
            super(ImuChannel, self).fromJson(json_dict)
            self.mode = json_dict.get('mode', self.mode)
            self.chan = json_dict.get('chan', self.chan)
            self.zeroValue = json_dict.get('zeroVal', self.zeroValue)
            self.alpha = json_dict.get('alpha', self.alpha)
            self.stale = False
        
    def toJson(self):
        json_dict = {}
        super(ImuChannel, self).appendJson(json_dict)
        json_dict['mode'] = self.mode
        json_dict['chan'] = self.chan
        json_dict['zeroVal'] = self.zeroValue
        json_dict['alpha'] = self.alpha
        return json_dict
    
IMU_CHANNEL_COUNT = 6
IMU_ACCEL_CHANNEL_IDS   = [0,1,2]
IMU_GYRO_CHANNEL_IDS    = [3,4,5]
IMU_MODE_DISABLED       = 0
IMU_MODE_NORMAL         = 1
IMU_MODE_INVERTED       = 2

class ImuConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = IMU_CHANNEL_COUNT
        self.channels = []
        
        for i in range(self.channelCount):
            self.channels.append(ImuChannel())

    def fromJson(self, imuConfigJson):
        for i in range (self.channelCount):
            imuChannelJson = imuConfigJson.get(str(i), None)
            if imuChannelJson:
                self.channels[i].fromJson(imuChannelJson)
                
    def toJson(self):
        imuCfgJson = {}
        for i in range (self.channelCount):
            imuChannel = self.channels[i]
            imuCfgJson[str(i)]=imuChannel.toJson()
            
        return {'imuCfg':imuCfgJson}
        
            
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
          
class LapConfigChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(LapConfigChannel, self).__init__(**kwargs)        
        
    def fromJson(self, json_dict):
        super(LapConfigChannel, self).fromJson(json_dict)        
        
    def toJson(self):
        json_dict = {}
        super(LapConfigChannel, self).appendJson(json_dict)
        return json_dict                
        
class LapConfig(object):
    DEFAULT_PREDICTED_TIME_SAMPLE_RATE = 5
    def __init__(self, **kwargs):
        self.stale = False
        self.lapCount = LapConfigChannel()
        self.lapTime = LapConfigChannel()
        self.predTime = LapConfigChannel()
        self.sector = LapConfigChannel()
        self.sectorTime = LapConfigChannel()
        self.elapsedTime = LapConfigChannel()
        self.currentLap = LapConfigChannel()

    def primary_stats_enabled(self):
        return (self.lapCount.sampleRate > 0 or 
            self.lapTime.sampleRate > 0 or 
            self.sector.sampleRate > 0 or 
            self.sectorTime.sampleRate > 0 or 
            self.elapsedTime.sampleRate > 0 or 
            self.currentLap.sampleRate > 0)
        
    def set_primary_stats(self, rate):
        self.lapCount.sampleRate = rate
        self.lapTime.sampleRate = rate
        self.sector.sampleRate = rate
        self.sectorTime.sampleRate = rate
        self.elapsedTime.sampleRate = rate
        self.currentLap.sampleRate = rate
        self.stale = True

    def predtime_stats_enabled(self):
        return self.predTime.sampleRate > 0 

    def fromJson(self, jsonCfg):
        if jsonCfg:
            lapCount = jsonCfg.get('lapCount')
            if lapCount:
                self.lapCount.fromJson(lapCount) 
                
            lapTime = jsonCfg.get('lapTime')
            if lapTime: 
                self.lapTime.fromJson(lapTime)
                
            predTime = jsonCfg.get('predTime')
            if predTime: 
                self.predTime.fromJson(predTime)
                
            sector = jsonCfg.get('sector')
            if sector: 
                self.sector.fromJson(sector)
                
            sectorTime = jsonCfg.get('sectorTime')
            if sectorTime: 
                self.sectorTime.fromJson(sectorTime)
            
            elapsedTime = jsonCfg.get('elapsedTime')
            if elapsedTime: 
                self.elapsedTime.fromJson(elapsedTime)

            currentLap = jsonCfg.get('currentLap')
            if currentLap: 
                self.currentLap.fromJson(currentLap)

            self.sanitize_config()

            self.stale = False

    """some config files are sneaking in bad values and they're making
    it up to the firmware config. UI doesn't allow editing of all of these
    values b/c we simplified the interface, so we need to compensate.
    This function will sanitize the configuration upon loading.

    Yes, this is a hack, for now. LapStats will change in the future
    when we break the API with a major version. When that breaks, lapstats
    will be updated to have only have two boolean values:
    stats_enabled and pred_time_enabled, and this sanitize function can
    be removed.

    Channel configuration data will not be editable.

    TODO: remove this sanitization upon 3.x API
    """
    def sanitize_config(self):
        self.lapCount.name = "LapCount"
        self.lapCount.units = ""
        self.lapCount.min = 0
        self.lapCount.max = 0
        self.lapCount.precision = 0

        self.lapTime.name = "LapTime"
        self.lapTime.units = "Min"
        self.lapTime.min = 0
        self.lapTime.max = 0
        self.lapTime.precision = 4

        self.sector.name = "Sector"
        self.sector.units = ""
        self.sector.min = 0
        self.sector.max = 0
        self.sector.precision = 0

        self.sectorTime.name = "SectorTime"
        self.sectorTime.units = "Min"
        self.sectorTime.min = 0
        self.sectorTime.max = 0
        self.sectorTime.precision = 4

        self.predTime.name = "PredTime"
        self.predTime.units = "Min"
        self.predTime.min = 0
        self.predTime.max = 0
        self.predTime.precision = 4

        self.elapsedTime.name = "ElapsedTime"
        self.elapsedTime.units = "Min"
        self.elapsedTime.min = 0
        self.elapsedTime.max = 0
        self.elapsedTime.precision = 4

        self.currentLap.name = "CurrentLap"
        self.currentLap.units = ""
        self.currentLap.min = 0
        self.currentLap.max = 0
        self.currentLap.precision = 0

    def toJson(self):
        lapCfgJson = {'lapCfg':{
                                  'lapCount': self.lapCount.toJson(),
                                  'lapTime': self.lapTime.toJson(),
                                  'predTime': self.predTime.toJson(),
                                  'sector': self.sector.toJson(),
                                  'sectorTime': self.sectorTime.toJson(),
                                  'elapsedTime': self.elapsedTime.toJson(),
                                  'currentLap': self.currentLap.toJson()
                                  }
                        }
        return lapCfgJson
          
class GpsConfig(object):
    GPS_QUALITY_NO_FIX = 0
    GPS_QUALITY_2D = 1
    GPS_QUALITY_3D = 2
    GPS_QUALITY_3D_DGNSS = 3

    def __init__(self, **kwargs):
        self.stale = False
        self.sampleRate = 0
        self.positionEnabled = False
        self.speedEnabled = False
        self.distanceEnabled = False
        self.altitudeEnabled = False
        self.satellitesEnabled = False
        self.qualityEnabled = False
        self.DOPEnabled = False

    def fromJson(self, json):
        if json:
            self.sampleRate = int(json.get('sr', self.sampleRate))
            self.positionEnabled = int(json.get('pos', self.positionEnabled))
            self.speedEnabled = int(json.get('speed', self.speedEnabled))
            self.distanceEnabled = int(json.get('dist', self.distanceEnabled))
            self.altitudeEnabled = int(json.get('alt', self.altitudeEnabled))
            self.satellitesEnabled = int(json.get('sats', self.satellitesEnabled))
            self.qualityEnabled = int(json.get('qual', self.qualityEnabled))
            self.DOPEnabled = int(json.get('dop', self.DOPEnabled))
            self.stale = False
            
    def toJson(self):
        gpsJson = {'gpsCfg':{
                              'sr' : self.sampleRate,
                              'pos' : self.positionEnabled,
                              'speed' : self.speedEnabled,
                              'dist' : self.distanceEnabled,
                              'alt' : self.altitudeEnabled,
                              'sats' : self.satellitesEnabled,
                              'qual' : self.qualityEnabled,
                              'dop' : self.DOPEnabled
                              }
                    }
                   
        return gpsJson
        
    
TIMER_CHANNEL_COUNT = 3

class TimerChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(TimerChannel, self).__init__(**kwargs)        
        self.mode = 0
        self.speed = 0
        self.pulsePerRev = 0
        self.slowTimer = 0
        self.alpha = 0
        
    def fromJson(self, json_dict):
        if json_dict:
            super(TimerChannel, self).fromJson(json_dict)            
            self.mode = json_dict.get('mode', self.mode)
            self.speed = json_dict.get('speed', self.speed)
            self.pulsePerRev = json_dict.get('ppr', self.pulsePerRev)
            self.slowTimer = json_dict.get('st', self.slowTimer)
            self.alpha = json_dict.get('alpha', self.alpha)            
            self.stale = False
            
    def toJson(self):
        json_dict = {}
        super(TimerChannel, self).appendJson(json_dict)        
        json_dict['mode'] = self.mode
        json_dict['ppr'] = self.pulsePerRev
        json_dict['speed'] = self.speed
        json_dict['st'] = self.slowTimer
        json_dict['alpha'] = self.alpha
        return json_dict

class TimerConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = TIMER_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(TimerChannel())   

    def fromJson(self, json):
        for i in range (self.channelCount):
            timerChannelJson = json.get(str(i), None)
            if timerChannelJson:
                self.channels[i].fromJson(timerChannelJson)
    
    def toJson(self):
        timerCfgJson = {}
        for i in range(TIMER_CHANNEL_COUNT):
            timerChannel = self.channels[i]
            timerCfgJson[str(i)] = timerChannel.toJson()
        return {'timerCfg':timerCfgJson}
        
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
        
class GpioChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(GpioChannel, self).__init__(**kwargs)        
        self.mode = 0
        
    def fromJson(self, json_dict):
        if json_dict:
            super(GpioChannel, self).fromJson(json_dict)            
            self.mode = json_dict.get('mode', self.mode)
            self.stale = False
            
    def toJson(self):
        json_dict = {}
        super(GpioChannel, self).appendJson(json_dict)        
        json_dict['mode'] = self.mode
        return json_dict
         
GPIO_CHANNEL_COUNT = 3

class GpioConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = GPIO_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(GpioChannel())   

    def fromJson(self, json):
        for i in range (self.channelCount):
            channelJson = json.get(str(i), None)
            if channelJson:
                self.channels[i].fromJson(channelJson)
                
    def toJson(self):
        gpioCfgJson = {}
        for i in range(GPIO_CHANNEL_COUNT):
            gpioChannel = self.channels[i]
            gpioCfgJson[str(i)] = gpioChannel.toJson()
        return {'gpioCfg':gpioCfgJson}
        
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
    
class PwmChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(PwmChannel, self).__init__(**kwargs)        
        self.outputMode = 0
        self.loggingMode = 0
        self.startupPeriod = 0
        self.startupDutyCycle = 0
        
    def fromJson(self, json_dict):
        if json_dict:
            super(PwmChannel, self).fromJson(json_dict)                        
            self.outputMode = json_dict.get('outMode', self.outputMode)
            self.loggingMode = json_dict.get('logMode', self.loggingMode)
            self.startupDutyCycle = json_dict.get('stDutyCyc', self.startupDutyCycle)
            self.startupPeriod = json_dict.get('stPeriod', self.startupPeriod)
            self.stale = False
            
    def toJson(self):
        json_dict = {}
        super(PwmChannel, self).appendJson(json_dict)        
        json_dict['outMode'] = self.outputMode
        json_dict['logMode'] = self.loggingMode
        json_dict['stDutyCyc'] = self.startupDutyCycle
        json_dict['stPeriod'] = self.startupPeriod
        return json_dict

PWM_CHANNEL_COUNT = 4   

class PwmConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = PWM_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(PwmChannel())   

    def fromJson(self, json):
        for i in range (self.channelCount):
            channelJson = json.get(str(i), None)
            if channelJson:
                self.channels[i].fromJson(channelJson)

    def toJson(self):
        pwmCfgJson = {}
        for i in range(PWM_CHANNEL_COUNT):
            pwmChannel = self.channels[i]
            pwmCfgJson[str(i)] = pwmChannel.toJson()
        return {'pwmCfg':pwmCfgJson}
        
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
        
CONFIG_SECTOR_COUNT = 20
        
TRACK_TYPE_CIRCUIT  = 0
TRACK_TYPE_STAGE    = 1

CONFIG_SECTOR_COUNT_CIRCUIT = 19
CONFIG_SECTOR_COUNT_STAGE = 18

class Track(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.trackId = None
        self.trackType = TRACK_TYPE_CIRCUIT
        self.sectorCount = CONFIG_SECTOR_COUNT
        self.startLine = GeoPoint()
        self.finishLine = GeoPoint()
        self.sectors = []
    
    def fromJson(self, trackJson):
        if trackJson:
            self.trackId = trackJson.get('id', self.trackId)
            self.trackType = trackJson.get('type', self.trackType)
            sectorsJson = trackJson.get('sec', None)
            del self.sectors[:]
            
            if self.trackType == TRACK_TYPE_CIRCUIT:
                self.startLine.fromJson(trackJson.get('sf', None))
                sectorCount = CONFIG_SECTOR_COUNT_CIRCUIT
            else:
                self.startLine.fromJson(trackJson.get('st', self.startLine))
                self.finishLine.fromJson(trackJson.get('fin', self.finishLine))
                sectorCount = CONFIG_SECTOR_COUNT_STAGE
    
            returnedSectorCount = len(sectorsJson)
            if sectorsJson:
                for i in range(sectorCount):
                    sector = GeoPoint()
                    if i < returnedSectorCount:
                        sectorJson = sectorsJson[i]
                        sector.fromJson(sectorJson)
                    self.sectors.append(sector)
            self.sectorCount = sectorCount
            self.stale = False
        
    @classmethod
    def fromTrackMap(cls, trackMap):
        t = Track()
        t.trackId = trackMap.short_id
        t.trackType = TRACK_TYPE_STAGE if trackMap.finish_point else TRACK_TYPE_CIRCUIT
        t.startLine = copy(trackMap.start_finish_point)
        t.finishLine = copy(trackMap.finish_point)

        maxSectorCount = CONFIG_SECTOR_COUNT_CIRCUIT if t.trackType == TRACK_TYPE_CIRCUIT else CONFIG_SECTOR_COUNT_STAGE
        sectorCount = 0
        for point in trackMap.sector_points:
            sectorCount += 1
            if sectorCount > maxSectorCount: break
            t.sectors.append(copy(point))
        return t
        
    def toJson(self):
        sectors = []
        for sector in self.sectors:
            sectors.append(sector.toJson())
        trackJson = {}
        trackJson['id'] = self.trackId
        trackJson['type'] = self.trackType
        trackJson['sec']  = sectors
        
        if self.trackType == TRACK_TYPE_STAGE:
            trackJson['st'] = self.startLine.toJson()
            trackJson['fin'] = self.finishLine.toJson()
        else:
            trackJson['sf'] = self.startLine.toJson()
        return trackJson
        
class TrackConfig(object):
    def __init__(self, **kwargs):
        self.stale=False
        self.track = Track()
        self.radius = 0
        self.autoDetect = 0
        
    def fromJson(self, trackConfigJson):
        if trackConfigJson:
            self.radius = trackConfigJson.get('rad', self.radius)
            self.autoDetect = trackConfigJson.get('autoDetect', self.autoDetect)
            
            trackJson = trackConfigJson.get('track', None)
            if trackJson:
                self.track = Track()
                self.track.fromJson(trackJson)
            self.stale = False
                    
    def toJson(self):
        trackCfgJson = {}
        trackCfgJson['rad'] = self.radius
        trackCfgJson['autoDetect'] = 1 if self.autoDetect else 0 
        trackCfgJson['track'] = self.track.toJson()

        return {'trackCfg':trackCfgJson}

class TracksDb(object):
    tracks = None
    def __init__(self, **kwargs):
        self.stale = False
        self.tracks = []
        
    def fromJson(self, tracksDbJson):
        if tracksDbJson:
            del self.tracks[:]
            tracksNode = tracksDbJson.get('tracks')
            if tracksNode:
                for trackNode in tracksNode:
                    track = Track()
                    track.fromJson(trackNode)
                    self.tracks.append(track)
            self.stale = False

    def toJson(self):
        tracksJson = []
        tracks = self.tracks
        for track in tracks:
            tracksJson.append(track.toJson())
        return {"trackDb":{'size':len(tracks),'tracks': tracksJson}}
  
class CanConfig(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.enabled = False
        self.baudRate = [0,0]
    
    def fromJson(self, canCfgJson):
        self.enabled = True if canCfgJson.get('en', self.enabled) == 1 else False
        bauds = canCfgJson.get('baud')
        self.baudRate = []
        for baud in bauds:
            self.baudRate.append(int(baud))
        self.stale = False
        
    def toJson(self):
        canCfgJson = {}
        canCfgJson['en'] = 1 if self.enabled else 0
        bauds = []
        for baud in self.baudRate:
            bauds.append(baud)
        canCfgJson['baud'] = bauds
        return {'canCfg':canCfgJson}        
            
class PidConfig(BaseChannel):
    def __init__(self, **kwargs):
        super(PidConfig, self).__init__(**kwargs)        
        self.pidId = 0
        
    def fromJson(self, json_dict):
        if json_dict:
            super(PidConfig, self).fromJson(json_dict)
            self.pid = json_dict.get("pid", self.pidId)
        
    def toJson(self):
        json_dict = {}
        super(PidConfig, self).appendJson(json_dict)
        json_dict['pid'] = self.pidId
        return json_dict

OBD2_CONFIG_MAX_PIDS = 20

class Obd2Config(object):
    pids = []
    enabled = False
    def __init__(self, **kwargs):
        self.stale = False
        self.enabled = False
    
    def fromJson(self, json_dict):
        self.enabled = json_dict.get('en', self.enabled) 
        pidsJson = json_dict.get("pids", None)
        if pidsJson:
            del self.pids[:]
            for pidJson in pidsJson:
                pid = PidConfig()
                pid.fromJson(pidJson)
                self.pids.append(pid)
                
    def toJson(self):
        pidsJson = []
        pidCount = len(self.pids)
        pidCount = pidCount if pidCount <= OBD2_CONFIG_MAX_PIDS else OBD2_CONFIG_MAX_PIDS
        
        for i in range(pidCount):
            pidsJson.append(self.pids[i].toJson())
            
        obd2Json =  {'obd2Cfg':{'en': 1 if self.enabled else 0, 'pids':pidsJson }}
        return obd2Json
        
class LuaScript(object):
    script = ""
    def __init__(self, **kwargs):
        self.stale = False
        pass
            
    def fromJson(self, jsonScript):
        self.script = jsonScript['data']
        self.stale = False
        
    def toJson(self):
        scriptJson = {"scriptCfg":{'data':self.script,'page':None}}
        return scriptJson
        
class BluetoothConfig(object):
    name = ""
    passKey = ""
    btEnabled = False
    def __init__(self, **kwargs):
        pass

    def fromJson(self, btCfgJson):
        self.btEnabled = btCfgJson['btEn'] == 1
        self.name = btCfgJson.get('name', self.name)
        self.passKey = btCfgJson.get('pass', self.passKey)
        
    def toJson(self):
        btCfgJson = {}
        btCfgJson['btEn'] = 1 if self.btEnabled else 0
        btCfgJson['name'] = self.name
        btCfgJson['passKey'] = self.passKey
        return btCfgJson 

class CellConfig(object):
    cellEnabled = False
    apnHost = ""
    apnUser = ""
    apnPass = ""
    def __init__(self, **kwargs):
        pass
    
    def fromJson(self, cellCfgJson):
        self.cellEnabled = cellCfgJson['cellEn'] == 1
        self.apnHost = cellCfgJson.get('apnHost', self.apnHost)
        self.apnUser = cellCfgJson.get('apnUser', self.apnUser)
        self.apnPass = cellCfgJson.get('apnPass', self.apnUser)

    def toJson(self):
        cellConfigJson = {}
        cellConfigJson['cellEn'] = 1 if self.cellEnabled else 0
        cellConfigJson['apnHost'] = self.apnHost
        cellConfigJson['apnUser'] = self.apnUser
        cellConfigJson['apnPass'] = self.apnPass
        return cellConfigJson        
    
class TelemetryConfig(object):
    deviceId = ""
    backgroundStreaming = 0
    
    def fromJson(self, telCfgJson):
        self.deviceId = telCfgJson.get('deviceId', self.deviceId)
        self.backgroundStreaming = True if telCfgJson.get('bgStream', 0) == 1 else False 
        
    def toJson(self):
        telCfgJson = {}
        telCfgJson['deviceId'] = self.deviceId
        telCfgJson['bgStream'] = 1 if self.backgroundStreaming else 0
        return telCfgJson
    
class ConnectivityConfig(object):
    stale = False
    bluetoothConfig = BluetoothConfig()
    cellConfig = CellConfig()
    telemetryConfig = TelemetryConfig()
    
    def fromJson(self, connCfgJson):
        btCfgJson = connCfgJson.get('btCfg')
        if btCfgJson:
            self.bluetoothConfig.fromJson(btCfgJson)
            
        cellCfgJson = connCfgJson.get('cellCfg')
        if cellCfgJson:
            self.cellConfig.fromJson(cellCfgJson)
            
        telCfgJson = connCfgJson.get('telCfg')
        if telCfgJson:
            self.telemetryConfig.fromJson(telCfgJson)
        self.stale = False
        
    def toJson(self):
        connCfgJson = {'btCfg' : self.bluetoothConfig.toJson(),
                       'cellCfg' : self.cellConfig.toJson(),
                       'telCfg' : self.telemetryConfig.toJson()}
        
        return {'connCfg':connCfgJson}


class VersionConfig(object):
    name = ''
    friendlyName = ''
    major = 0
    minor = 0
    bugfix = 0
    serial = 0
    def __init__(self, **kwargs):
        self.major = kwargs.get('major', 0)
        self.minor = kwargs.get('minor', 0)
        self.bugfix = kwargs.get('bugfix', 0)
    
    def __str__(self):
        return '{} {}.{}.{} (s/n# {})'.format(self.name, self.major, self.minor, self.bugfix, self.serial)
    
    def version_string(self):
        return '{}.{}.{}'.format(self.major, self.minor, self.bugfix)
            
    @staticmethod
    def get_minimum_version():
        return VersionConfig(major = RCP_COMPATIBLE_MAJOR_VERSION, minor = RCP_MINIMUM_MINOR_VERSION, bugfix = 0)
    
    def fromJson(self, versionJson):
        self.name = versionJson.get('name', self.name)
        self.friendlyName = versionJson.get('fname', self.friendlyName)
        self.major = versionJson.get('major', self.major)
        self.minor = versionJson.get('minor', self.minor)
        self.bugfix = versionJson.get('bugfix', self.bugfix)
        self.serial = versionJson.get('serial', self.serial)
        
    def toJson(self):
        versionJson = {'name': self.name, 'fname': self.friendlyName, 'major': self.major, 'minor': self.minor, 'bugfix': self.bugfix}
        return {'ver': versionJson}
    
    def is_compatible_version(self):
        return self.major == RCP_COMPATIBLE_MAJOR_VERSION and self.minor >= RCP_MINIMUM_MINOR_VERSION
    
class ChannelCapabilities(object):
    analog = 8
    imu = 6
    gpio = 3
    timer = 3
    pwm = 4
    can = 2

    def from_json_dict(self, json_dict):
        if json_dict:
            self.analog = int(json_dict.get('analog', self.analog))
            self.imu = int(json_dict.get('imu', self.imu))
            self.gpio = int(json_dict.get('gpio', self.gpio))
            self.pwm = int(json_dict.get('pwm', self.pwm))
            self.can = int(json_dict.get('can', self.can))
        
    def to_json_dict(self):
        return {'analog':self.analog,
                'imu':self.imu,
                'gpio':self.gpio,
                'timer':self.timer,
                'pwm':self.pwm,
                'can':self.can
                }
    
class SampleRateCapabilities(object):
    sensor = 1000
    gps = 50
    
    def from_json_dict(self, json_dict):
        if json_dict:
            self.sensor = json_dict.get('sensor', self.sensor)
            self.gps = json_dict.get('gps', self.gps)
    
    def to_json_dict(self):
        return {'gps': self.gps, 'sensor':self.sensor}
      
class StorageCapabilities():
    tracks = 240
    script = 10240
    
    def from_json_dict(self, json_dict):
        if json_dict:
            self.tracks = json_dict.get('tracks', self.tracks)
            self.script = json_dict.get('script', self.script)
        
    def to_json_dict(self):
        return {'tracks': self.tracks, 'script': self.script}
    
class Capabilities(object): 
    channels = ChannelCapabilities()
    sample_rates = SampleRateCapabilities()
    storage = StorageCapabilities()
    
    def from_json_dict(self, json_dict):
        if json_dict:
            channels = json_dict.get('channels')
            if channels:
                self.channels.from_json_dict(channels)
            
            sample_rates = json_dict.get('sampleRates')
            if sample_rates:
                self.sample_rates.from_json_dict(sample_rates)
                
            storage = json_dict.get('db')
            if storage:
                self.storage.from_json_dict(storage)
        
    def to_json_dict(self):
        return {'channels': self.channels.to_json_dict(),
                'sampleRates': self.sample_rates.to_json_dict(),
                'db': self.storage.to_json_dict() 
                }
    
class RcpConfig(object):
    loaded = False
    def __init__(self, **kwargs):
        
        self.versionConfig = VersionConfig()
        self.capabilities = Capabilities()
        self.analogConfig = AnalogConfig()
        self.imuConfig = ImuConfig()
        self.gpsConfig = GpsConfig()
        self.lapConfig = LapConfig()
        self.timerConfig = TimerConfig()
        self.gpioConfig = GpioConfig()
        self.pwmConfig = PwmConfig()
        self.trackConfig = TrackConfig()
        self.connectivityConfig = ConnectivityConfig()
        self.canConfig = CanConfig()
        self.obd2Config = Obd2Config()
        self.scriptConfig = LuaScript()
        self.trackDb = TracksDb()

    @property
    def stale(self):
        return  (self.analogConfig.stale or
                self.imuConfig.stale or
                self.gpsConfig.stale or
                self.lapConfig.stale or
                self.timerConfig.stale or
                self.gpioConfig.stale or
                self.pwmConfig.stale or
                self.trackConfig.stale or
                self.connectivityConfig.stale or
                self.canConfig.stale or
                self.obd2Config.stale or
                self.scriptConfig.stale or
                self.trackDb.stale)
    
    @stale.setter
    def stale(self, value):
        self.analogConfig.stale = value
        self.imuConfig.stale = value
        self.gpsConfig.stale = value
        self.lapConfig.stale = value
        self.timerConfig.stale = value
        self.gpioConfig.stale = value
        self.pwmConfig.stale = value
        self.trackConfig.stale = value
        self.connectivityConfig.stale = value
        self.canConfig.stale = value
        self.obd2Config.stale = value
        self.scriptConfig.stale = value
        self.trackDb.stale = value
        
    def fromJson(self, rcpJson):
        if rcpJson:
            rcpJson = rcpJson.get('rcpCfg', None)
            if rcpJson:
                versionJson = rcpJson.get('ver', None)
                if versionJson:
                    self.versionConfig.fromJson(versionJson)
        
                self.capabilities.from_json_dict(rcpJson.get('capabilities'))
                
                analogCfgJson = rcpJson.get('analogCfg', None)
                if analogCfgJson:
                    self.analogConfig.fromJson(analogCfgJson)
        
                timerCfgJson = rcpJson.get('timerCfg', None)
                if timerCfgJson:
                    self.timerConfig.fromJson(timerCfgJson)
                    
                imuCfgJson = rcpJson.get('imuCfg', None)
                if imuCfgJson:
                    self.imuConfig.fromJson(imuCfgJson)
                    
                lapCfgJson = rcpJson.get('lapCfg', None)
                if lapCfgJson:
                    self.lapConfig.fromJson(lapCfgJson)
                    
                gpsCfgJson = rcpJson.get('gpsCfg', None)
                if gpsCfgJson:
                    self.gpsConfig.fromJson(gpsCfgJson)
                    
                gpioCfgJson = rcpJson.get('gpioCfg', None)
                if gpioCfgJson:
                    self.gpioConfig.fromJson(gpioCfgJson)

                pwmCfgJson = rcpJson.get('pwmCfg', None)
                if pwmCfgJson:
                    self.pwmConfig.fromJson(pwmCfgJson)
                    
                trackCfgJson = rcpJson.get('trackCfg', None)
                if trackCfgJson:
                    self.trackConfig.fromJson(trackCfgJson)
                    
                connectivtyCfgJson = rcpJson.get('connCfg', None)
                if connectivtyCfgJson:
                    self.connectivityConfig.fromJson(connectivtyCfgJson)
                    
                canCfgJson = rcpJson.get('canCfg', None)
                if canCfgJson:
                    self.canConfig.fromJson(canCfgJson)
                    
                obd2CfgJson = rcpJson.get('obd2Cfg', None)
                if obd2CfgJson:
                    self.obd2Config.fromJson(obd2CfgJson)
                
                scriptJson = rcpJson.get('scriptCfg', None)
                if scriptJson:
                    self.scriptConfig.fromJson(scriptJson)
                    
                trackDbJson = rcpJson.get('trackDb', None)
                if trackDbJson:
                    self.trackDb.fromJson(trackDbJson)
                                        
                Logger.info('RcpConfig: Config version ' + str(self.versionConfig.major) + '.' + str(self.versionConfig.minor) + '.' + str(self.versionConfig.bugfix) + ' Loaded')
                self.loaded = True
    
    def fromJsonString(self, rcpJsonString):
        rcpJson = json.loads(rcpJsonString)
        self.fromJson(rcpJson)
        
    def toJsonString(self, pretty = True):
        return json.dumps(self.toJson(), sort_keys=True, indent=2, separators=(',', ': '))

    def toJson(self):
        rcpJson = {'rcpCfg':{
                             'ver': self.versionConfig.toJson().get('ver'),
                             'capabilities': self.capabilities.to_json_dict(),
                             'gpsCfg':self.gpsConfig.toJson().get('gpsCfg'),
                             'lapCfg':self.lapConfig.toJson().get('lapCfg'),
                             'imuCfg':self.imuConfig.toJson().get('imuCfg'),
                             'analogCfg':self.analogConfig.toJson().get('analogCfg'),
                             'timerCfg':self.timerConfig.toJson().get('timerCfg'),
                             'gpioCfg':self.gpioConfig.toJson().get('gpioCfg'),
                             'pwmCfg':self.pwmConfig.toJson().get('pwmCfg'),
                             'canCfg':self.canConfig.toJson().get('canCfg'),
                             'obd2Cfg':self.obd2Config.toJson().get('obd2Cfg'),
                             'connCfg':self.connectivityConfig.toJson().get('connCfg'),
                             'trackCfg':self.trackConfig.toJson().get('trackCfg'),
                             'scriptCfg':self.scriptConfig.toJson().get('scriptCfg'),
                             'trackDb': self.trackDb.toJson().get('trackDb')
                             }
                   }
        return rcpJson
