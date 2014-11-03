import io
import json
import traceback
import Queue
from time import sleep
from threading import Thread, RLock, Event
from autosportlabs.racecapture.config.rcpconfig import *
from functools import partial

CHANNEL_ADD_MODE_IN_PROGRESS = 1    
CHANNEL_ADD_MODE_COMPLETE = 2

TRACK_ADD_MODE_IN_PROGRESS = 1
TRACK_ADD_MODE_COMPLETE = 2

SCRIPT_ADD_MODE_IN_PROGRESS = 1
SCRIPT_ADD_MODE_COMPLETE = 2

DEFAULT_LEVEL2_RETRIES = 4
DEFAULT_MSG_RX_TIMEOUT = 5.0


class RcpCmd:
    name = None
    cmd = None
    payload = None
    index = None
    option = None
    def __init__(self, name, cmd, payload = None, index = None, option = None):
        self.name = name
        self.cmd = cmd
        self.payload = payload
        self.index = index
        self.option = option
            
class CommandSequence():
    command_list = None
    rootName = None
    winCallback = None
    failCallback = None    
            
class RcpApi:
    comms = None   
    msgListeners = {}
    cmdSequenceQueue = Queue.Queue()
    _command_queue = Queue.Queue()
    sendCommandLock = RLock()
    on_progress = lambda self, value: value
    on_tx = lambda self, value: None
    on_rx = lambda self, value: None
    level_2_retries = 0
    
    def __init__(self, **kwargs):
        self.comms = kwargs.get('comms', self.comms)
        self._running = Event()
        self._running.clear()

    def _start_message_rx_worker(self):
        self._running.set()
        self._rxThread = Thread(target=self.msgRxWorker)
        self._rxThread.daemon = True
        self._rxThread.start()

    def stop_msessage_rx_worker(self):
        print('Stopping msg rx worker')
        self._running.clear()
        self._rxThread.join()
        

    def initSerial(self, comms, detectWin, detectFail):
        self.comms = comms
        self._start_message_rx_worker()
        self.level_2_retries = 0                
        self.runAutoDetect(detectWin, detectFail)

    def detect_win(self, detect_win, version_info):
        self.level_2_retries = DEFAULT_LEVEL2_RETRIES
        detect_win(version_info)
        
    def runAutoDetect(self, detect_win=None, detect_fail=None):
        self.comms.autoDetect(self.getVersion, lambda version_info: self.detect_win(detect_win, version_info), detect_fail)

    def addListener(self, messageName, callback):
        listeners = self.msgListeners.get(messageName, None)
        if listeners:
            listeners.add(callback)
        else:
            listeners = set()
            listeners.add(callback)
            self.msgListeners[messageName] = listeners

    def removeListener(self, messageName, callback):
        listeners = self.msgListeners.get(messageName, None)
        if listeners:
            listeners.discard(callback)
            
    def msgRxWorker(self):
        print('msgRxWorker started')
        retryMax = 3
        retries = 0
        msg = ''
        comms = self.comms
        while self._running.is_set():
            try:
                msg += comms.read(1)
                if msg[-2:] == '\r\n':
                    msg = msg[:-2]
                    print('msgRxWorker Rx: ' + str(msg))
                    msgJson = json.loads(msg, strict = False)
                    self.on_rx(True)
                    retries = 0
                    for messageName in msgJson.keys():
                        print('processing message ' + messageName)
                        listeners = self.msgListeners.get(messageName, None)
                        if listeners:
                            for listener in listeners:
                                listener(msgJson)
                                break
                    msg = ''
            except Exception:
                print('Message Rx Exception: ' + str(Exception))
                traceback.print_exc()
                sleep(0.5)
                    
        print("RxWorker exiting")
                    
    def rcpCmdComplete(self, msgReply):
        self.cmdSequenceQueue.put(msgReply)
                
    def recoverTimeout(self):
        print('POKE')
        self.comms.write(' ')
        
    def executeSingle(self, cmd, win_callback, fail_callback):
        command = CommandSequence()
        command.command_list = [cmd]
        command.rootName = None
        command.winCallback = win_callback
        command.failCallback = fail_callback
        self._command_queue.put(command)
        
    def _queue_multiple(self, command_list, root_name, win_callback, fail_callback):
        command = CommandSequence()
        command.command_list = command_list
        command.rootName = root_name
        command.winCallback = win_callback
        command.failCallback = fail_callback
        
    def notifyProgress(self, count, total):
        if self.on_progress:
            self.on_progress((float(count) / float(total)) * 100)
        
    def executeSequence(self):

        while True:
            try:
                command = self._command_queue.get() #this blocks forever
                
                command_list = command.command_list
                rootName = command.rootName
                winCallback = command.winCallback
                failCallback = command.failCallback
                
                print('Execute Sequence begin')
                        
                q = self.cmdSequenceQueue
                
                responseResults = {}
                cmdCount = 0
                cmdLength = len(command_list)
                self.notifyProgress(cmdCount, cmdLength)
                try:
                    for rcpCmd in command_list:
                        payload = rcpCmd.payload
                        index = rcpCmd.index
                        option = rcpCmd.option
        
                        level2Retry = 0
                        name = rcpCmd.name
                        result = None
                        
                        self.addListener(name, self.rcpCmdComplete)
                        while not result and level2Retry <= self.level_2_retries:
                            if not payload == None and not index == None and not option == None:
                                rcpCmd.cmd(payload, index, option)
                            elif not payload == None and not index == None:
                                rcpCmd.cmd(payload, index)
                            elif not payload == None:
                                rcpCmd.cmd(payload)
                            else:
                                rcpCmd.cmd()
        
                            retry = 0
                            while not result and retry < self.comms.DEFAULT_READ_RETRIES:
                                try:
                                    result = q.get(True, DEFAULT_MSG_RX_TIMEOUT)
                                    msgName = result.keys()[0]
                                    if not msgName == name:
                                        print('rx message did not match expected name ' + str(name) + '; ' + str(msgName))
                                        result = None
                                except Exception as e:
                                    print('Read message timeout ' + str(e))
                                    self.recoverTimeout()
                                    retry += 1
                            if not result:
                                print('Level 2 retry for ' + name)
                                level2Retry += 1
        
        
                        if not result:
                            raise Exception('Timeout waiting for ' + name)
                                    
                                            
                        responseResults[name] = result[name]
                        self.removeListener(name, self.rcpCmdComplete)
                        cmdCount += 1
                        self.notifyProgress(cmdCount, cmdLength)
                        
                    if rootName:
                        winCallback({rootName: responseResults})
                    else:
                        winCallback(responseResults)
                except Exception as detail:
                    print('Command sequence exception: ' + str(detail))
                    traceback.print_exc()
                    failCallback(detail)

                print('Execute Sequence complete')
                
            except Exception as e:
                print('Execute command exception ' + str(e))
                
    def sendCommand(self, cmd):
        try:
            self.sendCommandLock.acquire()
            rsp = None
            
            comms = self.comms
            comms.flushOutput()
            comms.flushInput()

            cmdStr = json.dumps(cmd, separators=(',', ':')) + '\r'
            print('send cmd: ' + cmdStr)
            comms.write(cmdStr)
        finally:
            self.sendCommandLock.release()
            self.on_tx(True)
        
    def sendGet(self, name, index = None):
        if index == None:
            index = None
        else:
            index = str(index)
        cmd = {name:index}
        self.sendCommand(cmd)

    def sendSet(self, name, payload, index = None):
        if not index == None:
            self.sendCommand({name: {str(index): payload}})            
        else:
            self.sendCommand({name: payload})
                            
    def getRcpCfgCallback(self, cfg, rcpCfgJson, winCallback):
        cfg.fromJson(rcpCfgJson)
        winCallback(cfg)
        
    def getRcpCfg(self, cfg, winCallback, failCallback):
        cmdSequence = [       RcpCmd('ver',         self.sendGetVersion),
                              RcpCmd('analogCfg',   self.getAnalogCfg),
                              RcpCmd('imuCfg',      self.getImuCfg),
                              RcpCmd('gpsCfg',      self.getGpsCfg),
                              RcpCmd('lapCfg',      self.getLapCfg),
                              RcpCmd('timerCfg',    self.getTimerCfg),
                              RcpCmd('gpioCfg',     self.getGpioCfg),
                              RcpCmd('pwmCfg',      self.getPwmCfg),
                              RcpCmd('trackCfg',    self.getTrackCfg),
                              RcpCmd('canCfg',      self.getCanCfg),
                              RcpCmd('obd2Cfg',     self.getObd2Cfg),
                              RcpCmd('scriptCfg',   self.getScript),
                              RcpCmd('connCfg',     self.getConnectivityCfg),
                              RcpCmd('trackDb',     self.getTrackDb),
                              RcpCmd('channels',    self.getChannels)
                           ]
                
        t = Thread(target=self.executeSequence, args=(cmdSequence, 'rcpCfg', lambda rcpJson: self.getRcpCfgCallback(cfg, rcpJson, winCallback), failCallback))
        t.daemon = True
        t.start()
            
        
    def writeRcpCfg(self, cfg, winCallback = None, failCallback = None):
        cmdSequence = []
        
        connCfg = cfg.connectivityConfig
        if connCfg.stale:
            cmdSequence.append(RcpCmd('setConnCfg', self.setConnectivityCfg, connCfg.toJson()))

        gpsCfg = cfg.gpsConfig
        if gpsCfg.stale:
            cmdSequence.append(RcpCmd('setGpsCfg', self.setGpsCfg, gpsCfg.toJson()))
        
        lapCfg = cfg.lapConfig
        if lapCfg.stale:
            cmdSequence.append(RcpCmd('setLapCfg', self.setLapCfg, lapCfg.toJson()))

        imuCfg = cfg.imuConfig
        for i in range(IMU_CHANNEL_COUNT):
            imuChannel = imuCfg.channels[i]
            if imuChannel.stale:
                cmdSequence.append(RcpCmd('setImuCfg', self.setImuCfg, imuChannel.toJson(), i))
                
        analogCfg = cfg.analogConfig
        for i in range(ANALOG_CHANNEL_COUNT):
            analogChannel = analogCfg.channels[i]
            if analogChannel.stale:
                cmdSequence.append(RcpCmd('setAnalogCfg', self.setAnalogCfg, analogChannel.toJson(), i))
        
        timerCfg = cfg.timerConfig
        for i in range(TIMER_CHANNEL_COUNT):
            timerChannel = timerCfg.channels[i]
            if timerChannel.stale:
                cmdSequence.append(RcpCmd('setTimerCfg', self.setTimerCfg, timerChannel.toJson(), i))
        
        gpioCfg = cfg.gpioConfig
        for i in range(GPIO_CHANNEL_COUNT):
            gpioChannel = gpioCfg.channels[i]
            if gpioChannel.stale:
                cmdSequence.append(RcpCmd('setGpioCfg', self.setGpioCfg, gpioChannel.toJson(), i))
                 
        pwmCfg = cfg.pwmConfig
        for i in range(PWM_CHANNEL_COUNT):
            pwmChannel = pwmCfg.channels[i]
            if pwmChannel.stale:
                cmdSequence.append(RcpCmd('setPwmCfg', self.setPwmCfg, pwmChannel.toJson(), i))

        canCfg = cfg.canConfig
        if canCfg.stale:
            cmdSequence.append(RcpCmd('setCanCfg', self.setCanCfg, canCfg.toJson()))

        obd2Cfg = cfg.obd2Config
        if obd2Cfg.stale:
            cmdSequence.append(RcpCmd('setObd2Cfg', self.setObd2Cfg, obd2Cfg.toJson()))
            
        trackCfg = cfg.trackConfig
        if trackCfg.stale:
            cmdSequence.append(RcpCmd('setTrackCfg', self.setTrackCfg, trackCfg.toJson()))
            
        scriptCfg = cfg.scriptConfig
        if scriptCfg.stale:
            self.sequenceWriteScript(scriptCfg.toJson(), cmdSequence)
            
        trackDb = cfg.trackDb
        if trackDb.stale:
            self.sequenceWriteTrackDb(trackDb.toJson(), cmdSequence)
        
        channels = cfg.channels
        if channels.stale:
            self.sequenceWriteChannels(channels.toJson(), cmdSequence)
        
        cmdSequence.append(RcpCmd('flashCfg', self.sendFlashConfig))
                
        t = Thread(target=self.executeSequence, args=(cmdSequence, 'setRcpCfg', winCallback, failCallback,))
        t.daemon = True
        t.start()


    def resetDevice(self, bootloader=False):
        if bootloader:
            loaderint = 1
        else:
            loaderint = 0
            
        self.sendCommand({'sysReset': {'loader':loaderint}})
                
    def getAnalogCfg(self, channelId = None):
        self.sendGet('getAnalogCfg', channelId)

    def setAnalogCfg(self, analogCfg, channelId):
        self.sendSet('setAnalogCfg', analogCfg, channelId)

    def getImuCfg(self, channelId = None):
        self.sendGet('getImuCfg', channelId)
    
    def setImuCfg(self, imuCfg, channelId):
        self.sendSet('setImuCfg', imuCfg, channelId)
    
    def getLapCfg(self):
        self.sendGet('getLapCfg', None)
    
    def setLapCfg(self, lapCfg):
        self.sendSet('setLapCfg', lapCfg)

    def getGpsCfg(self):
        self.sendGet('getGpsCfg', None)
    
    def setGpsCfg(self, gpsCfg):
        self.sendSet('setGpsCfg', gpsCfg)
        
    def getTimerCfg(self, channelId = None):
        self.sendGet('getTimerCfg', channelId)
    
    def setTimerCfg(self, timerCfg, channelId):
        self.sendSet('setTimerCfg', timerCfg, channelId)
    
    def setGpioCfg(self, gpioCfg, channelId):
        self.sendSet('setGpioCfg', gpioCfg, channelId)
        
    def getGpioCfg(self, channelId = None):
        self.sendGet('getGpioCfg', channelId)
    
    def getPwmCfg(self, channelId = None):
        self.sendGet('getPwmCfg', channelId)
    
    def setPwmCfg(self, pwmCfg, channelId):
        self.sendSet('setPwmCfg', pwmCfg, channelId)
        
    def getTrackCfg(self):
        self.sendGet('getTrackCfg', None)
    
    def setTrackCfg(self, trackCfg):
        self.sendSet('setTrackCfg', trackCfg)
    
    def getCanCfg(self):
        self.sendGet('getCanCfg', None)
    
    def setCanCfg(self, canCfg):
        self.sendSet('setCanCfg', canCfg)
    
    def getObd2Cfg(self):
        self.sendGet('getObd2Cfg', None)
    
    def setObd2Cfg(self, obd2Cfg):
        self.sendSet('setObd2Cfg', obd2Cfg)
    
    def getConnectivityCfg(self):
        self.sendGet('getConnCfg', None)
    
    def setConnectivityCfg(self, connCfg):
        self.sendSet('setConnCfg', connCfg)
    
    def getScript(self):
        self.sendGet('getScriptCfg', None)

    def setScriptPage(self, scriptPage, page, mode):
        self.sendCommand({'setScriptCfg': {'data':scriptPage,'page':page, 'mode':mode}})
        
    def sequenceWriteScript(self, scriptCfg, cmdSequence):
        page = 0
        print(str(scriptCfg))
        script = scriptCfg['scriptCfg']['data']
        while True:
            if len(script) >= 256:
                scr = script[:256]
                script = script[256:]
                mode = SCRIPT_ADD_MODE_IN_PROGRESS if len(script) > 0 else SCRIPT_ADD_MODE_COMPLETE
                cmdSequence.append(RcpCmd('setScriptCfg', self.setScriptPage, scr, page, mode))
                page = page + 1
            else:
                cmdSequence.append(RcpCmd('setScriptCfg', self.setScriptPage, script, page, SCRIPT_ADD_MODE_COMPLETE))
                break
        
    def sendRunScript(self):
        self.sendCommand({'runScript': None})
        
    def runScript(self, winCallback, failCallback):
        self.executeSingle(RcpCmd('runScript', self.sendRunScript), winCallback, failCallback)
        
    def setLogfileLevel(self, level, winCallback = None, failCallback = None):
        def setLogfileLevelCmd():
            self.sendCommand({'setLogfileLevel': {'level':level}})
            
        if winCallback and failCallback:
            self.executeSingle(RcpCmd('logfileLevel', setLogfileLevelCmd), winCallback, failCallback)
        else:
            setLogfileLevelCmd()
        
    def getLogfile(self, winCallback = None, failCallback = None):
        def getLogfileCmd():
            self.sendCommand({'getLogfile': None})
            
        if winCallback and failCallback:
            self.executeSingle(RcpCmd('logfile', getLogfileCmd), winCallback, failCallback)
        else:
            getLogfileCmd()
            
    def sendFlashConfig(self):
        self.sendCommand({'flashCfg': None})

    def getChannels(self):
        self.sendGet('getChannels')
        
    def getChannelList(self, winCallback, failCallback):
        cmdSequence = [ RcpCmd('channels', self.getChannels) ]
        t = Thread(target=self.executeSequence, args=(cmdSequence, None, winCallback, failCallback))
        t.daemon = True
        t.start()
                
    def sequenceWriteChannels(self, channels, cmdSequence):
        
        channels = channels.get('channels', None)
        if channels:
            index = 0
            channelCount = len(channels)
            for channel in channels:
                mode = CHANNEL_ADD_MODE_IN_PROGRESS if index < channelCount - 1 else CHANNEL_ADD_MODE_COMPLETE
                cmdSequence.append(RcpCmd('addChannel', self.addChannel, channel, index, mode))
                index += 1        
                    
    def addChannel(self, channelJson, index, mode):
        return self.sendCommand({'addChannel': 
                                 {'index': index, 
                                 'mode': mode,
                                 'channel': channelJson
                                 }
                                 })
    
    def sequenceWriteTrackDb(self, tracksDbJson, cmdSequence):
        trackDbJson = tracksDbJson.get('trackDb')
        if trackDbJson:
            index = 0
            tracksJson = trackDbJson.get('tracks')
            if tracksJson:
                trackCount = len(tracksJson)
                for trackJson in tracksJson:
                    mode = TRACK_ADD_MODE_IN_PROGRESS if index < trackCount - 1 else TRACK_ADD_MODE_COMPLETE
                    cmdSequence.append(RcpCmd('addTrackDb', self.addTrackDb, trackJson, index, mode))
                    index += 1
    
    def addTrackDb(self, trackJson, index, mode):
        return self.sendCommand({'addTrackDb':
                                 {'index':index, 
                                  'mode':mode, 
                                  'track': trackJson
                                  }
                                 })

    def getTrackDb(self):
        self.sendGet('getTrackDb')

    def sendGetVersion(self):
        rsp = self.sendCommand({"getVer":None})

    def getVersion(self, winCallback, failCallback):
        print('in getVersion')
        self.executeSingle(RcpCmd('ver', self.sendGetVersion), winCallback, failCallback)

    def sample(self, includeMeta):
        if includeMeta:
            self.sendCommand({'s':{'meta':1}})
        else:
            self.sendCommand({'s':0})
