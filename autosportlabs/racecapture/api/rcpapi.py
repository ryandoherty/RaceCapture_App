import io
import json
import traceback
import Queue
from time import sleep
from threading import Thread, RLock, Event
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.comms.commscommon import PortNotOpenException, CommsErrorException
from functools import partial
from kivy.clock import Clock
from kivy.logger import Logger
from traceback import print_stack

TRACK_ADD_MODE_IN_PROGRESS      = 1
TRACK_ADD_MODE_COMPLETE         = 2

SCRIPT_ADD_MODE_IN_PROGRESS     = 1
SCRIPT_ADD_MODE_COMPLETE        = 2

DEFAULT_LEVEL2_RETRIES          = 3
DEFAULT_MSG_RX_TIMEOUT          = 1

AUTODETECT_COOLOFF_TIME         = 1
AUTODETECT_LEVEL2_RETRIES       = 1
DEFAULT_READ_RETRIES            = 2

COMMS_KEEP_ALIVE_TIMEOUT        = 2

NO_DATA_AVAILABLE_DELAY         = 0.1
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
    detect_win_callback = None
    detect_fail_callback = None
    detect_activity_callback = None
    comms = None
    msgListeners = {}
    cmdSequenceQueue = Queue.Queue()
    _command_queue = Queue.Queue()
    sendCommandLock = RLock()
    on_progress = lambda self, value: value
    on_tx = lambda self, value: None
    on_rx = lambda self, value: None
    level_2_retries = DEFAULT_LEVEL2_RETRIES
    msg_rx_timeout = DEFAULT_MSG_RX_TIMEOUT
    _cmd_sequence_thread = None
    _msg_rx_thread = None
    _auto_detect_event = Event()
    _auto_detect_busy = Event()

    def __init__(self, **kwargs):
        self.comms = kwargs.get('comms', self.comms)
        self._running = Event()
        self._running.clear()
        self._enable_autodetect = Event()
        self._enable_autodetect.set()
        self._disconnect_callback = kwargs.get('on_disconnect')

    def enable_autorecover(self):
        Logger.info("RCPAPI: Enabling auto recover")
        self._enable_autodetect.set()

    def disable_autorecover(self):
        Logger.info("RCPAPI: Disabling auto recover")
        self._enable_autodetect.clear()

    def recover_connection(self):
        if self._disconnect_callback:
            self._disconnect_callback()

        if self._enable_autodetect.is_set():
            Logger.info("RCPAPI: attempting to recover connection")
            self.run_auto_detect()

    def _start_message_rx_worker(self):
        self._running.set()
        self._msg_rx_thread = Thread(target=self.msg_rx_worker)
        self._msg_rx_thread.daemon = True
        self._msg_rx_thread.start()

    def stop_message_rx_worker(self):
        Logger.info('RCPAPI: Stopping msg rx worker')
        self._running.clear()
        self._msg_rx_thread.join()

    def _start_cmd_sequence_worker(self):
        self._cmd_sequence_thread = Thread(target=self.cmd_sequence_worker)
        self._cmd_sequence_thread.daemon = True
        self._cmd_sequence_thread.start()

    def init_comms(self, comms):
        self.comms = comms
        self._start_message_rx_worker()
        self._start_cmd_sequence_worker()
        self.start_auto_detect_worker()
        Clock.schedule_interval(lambda dt: comms.keep_alive(), COMMS_KEEP_ALIVE_TIMEOUT)

    def cleanup_comms(self):
        self.comms.cleanup()

    def shutdown_comms(self):
        Logger.info('RCPAPI: shutting down comms')
        try:
            self.comms.close()
            self.comms.port = None
        except:
            pass

    def detect_win(self, version_info):
        self.level_2_retries = DEFAULT_LEVEL2_RETRIES
        self.msg_rx_timeout = DEFAULT_MSG_RX_TIMEOUT
        if self.detect_win_callback: self.detect_win_callback(version_info)

    def run_auto_detect(self):
        self.level_2_retries = AUTODETECT_LEVEL2_RETRIES
        self.msg_rx_timeout = self.comms.CONNECT_TIMEOUT
        self._auto_detect_event.set()

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

    def msg_rx_worker(self):
        Logger.info('RCPAPI: msg_rx_worker started')
        comms = self.comms
        error_count = 0
        while self._running.is_set():
            msg = None
            try:
                msg = comms.read_message()
                if msg:
                    #clean incoming string, and drop illegal characters
                    msg = unicode(msg, errors='ignore')
                    Logger.debug('RCPAPI: Rx: ' + str(msg))
                    msgJson = json.loads(msg, strict = False)
                    self.on_rx(True)
                    error_count = 0
                    for messageName in msgJson.keys():
                        Logger.trace('RCPAPI: processing message ' + messageName)
                        listeners = self.msgListeners.get(messageName, None)
                        if listeners:
                            for listener in listeners:
                                try:
                                    listener(msgJson)
                                except Exception as e:
                                    Logger.error('RCPAPI: Message Listener Exception for')
                                    Logger.debug(traceback.format_exc())
                            break
                    msg = ''
                else:
                    sleep(NO_DATA_AVAILABLE_DELAY)

            except PortNotOpenException:
                Logger.debug("RCPAPI: Port not open...")
                msg=''
                sleep(1.0)
            except Exception:
                Logger.warn('RCPAPI: Message rx worker exception: {} | {}'.format(msg, str(Exception)))
                Logger.debug(traceback.format_exc())
                msg = ''
                error_count += 1
                if error_count > 5 and not self._auto_detect_event.is_set():
                    Logger.warn("RCPAPI: Too many Rx exceptions; re-opening connection")
                    self.recover_connection()
                    sleep(5)
                else:
                    sleep(0.25)

        Logger.info("RCPAPI: RxWorker exiting")

    def rcpCmdComplete(self, msgReply):
        self.cmdSequenceQueue.put(msgReply)

    def recoverTimeout(self):
        Logger.warn('RCPAPI: POKE')
        self.comms.write_message(' ')

    def notifyProgress(self, count, total):
        if self.on_progress:
            self.on_progress((float(count) / float(total)) * 100)

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
        self._command_queue.put(command)

    def cmd_sequence_worker(self):
        while True:
            try:
                command = self._command_queue.get() #this blocks forever

                command_list = command.command_list
                rootName = command.rootName
                winCallback = command.winCallback
                failCallback = command.failCallback
                comms = self.comms

                Logger.info('RCPAPI: Execute Sequence begin')

                if not comms.isOpen(): self.run_auto_detect()

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
                            while not result and retry < DEFAULT_READ_RETRIES:
                                try:
                                    result = q.get(True, self.msg_rx_timeout)
                                    msgName = result.keys()[0]
                                    if not msgName == name:
                                        Logger.info('RCPAPI: rx message did not match expected name ' + str(name) + '; ' + str(msgName))
                                        result = None
                                except Exception as e:
                                    Logger.info('RCPAPI: Read message timeout ' + str(e))
                                    self.recoverTimeout()
                                    retry += 1
                            if not result:
                                Logger.info('RCPAPI: Level 2 retry for (' + str(level2Retry) + ') ' + name)
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

                except CommsErrorException:
                    self.recover_connection()
                except Exception as detail:
                    Logger.error('RCPAPI: Command sequence exception: ' + str(detail))
                    Logger.debug(traceback.format_exc())
                    failCallback(detail)
                    self.recover_connection()

                Logger.info('RCPAPI: Execute Sequence complete')

            except Exception as e:
                Logger.error('RCPAPI: Execute command exception ' + str(e))

    def sendCommand(self, cmd):
        try:
            self.sendCommandLock.acquire()
            rsp = None

            comms = self.comms

            cmdStr = json.dumps(cmd, separators=(',', ':')) + '\r'

            Logger.debug('RCPAPI: Tx: ' + cmdStr)
            comms.write_message(cmdStr)
        except Exception:
            self.recover_connection()
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
                              RcpCmd('capabilities',self.getCapabilities),
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
                              RcpCmd('trackDb',     self.getTrackDb)
                           ]

        self._queue_multiple(cmdSequence, 'rcpCfg', lambda rcpJson: self.getRcpCfgCallback(cfg, rcpJson, winCallback), failCallback)

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

        cmdSequence.append(RcpCmd('flashCfg', self.sendFlashConfig))

        self._queue_multiple(cmdSequence, 'setRcpCfg', winCallback, failCallback)

    def resetDevice(self, bootloader=False, reset_delay=0):
        if bootloader:
            loaderint = 1
        else:
            loaderint = 0

        self.sendCommand({'sysReset': {'loader':loaderint, 'delay':reset_delay}})

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

    def get_status(self):
        self.sendGet('getStatus', None)

    def sequenceWriteScript(self, scriptCfg, cmdSequence):
        page = 0
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
            else:
                cmdSequence.append(RcpCmd('addTrackDb', self.addTrackDb, [], index, TRACK_ADD_MODE_COMPLETE))

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
        self.sendCommand({"getVer":None})

    def getVersion(self, winCallback, failCallback):
        self.executeSingle(RcpCmd('ver', self.sendGetVersion), winCallback, failCallback)

    def getCapabilities(self):
        self.sendGet('getCapabilities')

    def sendCalibrateImu(self):
        self.sendCommand({"calImu":1})

    def calibrate_imu(self, winCallback, failCallback):
        cmd_sequence = []
        cmd_sequence.append(RcpCmd('calImu', self.sendCalibrateImu))
        cmd_sequence.append(RcpCmd('flashCfg', self.sendFlashConfig))
        self._queue_multiple(cmd_sequence, 'calImu', winCallback, failCallback)

    def get_meta(self):
        Logger.info("RCPAPI: sending meta")
        self.sendCommand({'getMeta':None})

    def sample(self, include_meta=False):
        if include_meta:
            self.sendCommand({'s':{'meta':1}})
        else:
            self.sendCommand({'s':0})

    def start_auto_detect_worker(self):
        self._auto_detect_event.clear()
        t = Thread(target=self.auto_detect_worker)
        t.daemon = True
        t.start()

    def auto_detect_worker(self):

        class VersionResult(object):
            version_json = None

        def on_ver_win(value):
            version_result.version_json = value
            version_result_event.set()

        while True:
            try:
                self._auto_detect_event.wait()
                self._auto_detect_event.clear()
                self._enable_autodetect.wait()
                Logger.info("RCPAPI: Starting auto-detect")
                self._auto_detect_busy.set()
                self.sendCommandLock.acquire()
                self.addListener("ver", on_ver_win)

                comms = self.comms
                if comms and comms.isOpen():
                    comms.close()

                version_result = VersionResult()
                version_result_event = Event()
                version_result_event.clear()

                if comms.port:
                    ports = [comms.port]
                else:
                    ports = comms.get_available_ports()
                    Logger.info('RCPAPI: Searching for device on all ports')

                testVer = VersionConfig()
                for p in ports:
                    try:
                        Logger.info('RCPAPI: Trying ' + str(p))
                        if self.detect_activity_callback: self.detect_activity_callback(str(p))
                        comms.port = p
                        comms.open()
                        self.sendGetVersion()
                        version_result_event.wait(1)
                        version_result_event.clear()
                        if version_result.version_json != None:
                            testVer.fromJson(version_result.version_json.get('ver', None))
                            if testVer.major > 0 or testVer.minor > 0 or testVer.bugfix > 0:
                                break #we found something!
                        else:
                            try:
                                Logger.warn('RCPAPI: Giving up on ' + str(p))
                                comms.close()
                            finally:
                                pass

                    except Exception as detail:
                        Logger.error('RCPAPI: Not found on ' + str(p) + " " + str(detail))
                        try:
                            comms.close()
                        finally:
                            pass

                if version_result.version_json != None:
                    Logger.info("RCPAPI: Found device version " + str(testVer) + " on port: " + str(comms.port))
                    self.detect_win(testVer)
                    self._auto_detect_event.clear()
                else:
                    Logger.info('RCPAPI: Did not find device')
                    comms.close()
                    comms.port = None
                    if self.detect_fail_callback: self.detect_fail_callback()
            except Exception as e:
                Logger.error('RCPAPI: Error running auto detect: ' + str(e))
                Logger.debug(traceback.format_exc())
            finally:
                Logger.info("RCPAPI: auto detect finished. port=" + str(comms.port))
                self._auto_detect_busy.clear()
                self.removeListener("ver", on_ver_win)
                self.sendCommandLock.release()
                sleep(AUTODETECT_COOLOFF_TIME)
