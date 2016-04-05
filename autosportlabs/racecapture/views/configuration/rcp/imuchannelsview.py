import kivy
kivy.require('1.9.1')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.uix.spinner import Spinner
from mappedspinner import MappedSpinner
from utils import *
from valuefield import IntegerValueField, FloatValueField
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.widgets.scrollcontainer import ScrollContainer
import traceback

IMU_CHANNELS_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/imuchannelsview.kv'

class OrientationSpinner(MappedSpinner):
    def __init__(self, **kwargs):
        super(OrientationSpinner, self).__init__(**kwargs)
        self.setValueMap({1:'Normal', 2:'Inverted'}, '')

class ImuMappingSpinner(MappedSpinner):
    def __init__(self, **kwargs):
        super(ImuMappingSpinner, self).__init__(**kwargs)

    def setImuType(self, imuType):
        if imuType == 'accel':
            self.setValueMap({0:'X', 1:'Y', 2:'Z'}, 'X')
        elif imuType == 'gyro':
            self.setValueMap({3:'Yaw', 4:'Pitch', 5:'Roll'}, 'Yaw')
        
class ImuChannel(BoxLayout):
    channelConfig = None
    channelLabels = []
    def __init__(self, **kwargs):
        super(ImuChannel, self).__init__(**kwargs)
        self.imu_id = kwargs.get('imu_id', None)
        self.register_event_type('on_modified')
    
    def on_modified(self):
        pass
    
    def enable_view(self, enabled):
        disabled = not enabled
        kvFind(self, 'rcid', 'orientation').disabled = disabled
        kvFind(self, 'rcid', 'mapping').disabled = disabled
        kvFind(self, 'rcid', 'zeroValue').disabled = disabled

    def on_zero_value(self, instance, value):
        if self.channelConfig:
            self.channelConfig.zeroValue = int(value)
            self.channelConfig.stale = True
            self.dispatch('on_modified')
                
    def on_orientation(self, instance, value):
        if self.channelConfig and value:
            mode = int(instance.getValueFromKey(value))
            if mode:
                self.channelConfig.mode = mode
                self.channelConfig.stale = True
                self.dispatch('on_modified')
                
    def on_mapping(self, instance, value):
        if self.channelConfig:
            self.channelConfig.chan = int(instance.getValueFromKey(value))
            self.channelConfig.stale = True
            self.dispatch('on_modified')
                            
    def on_enabled(self, instance, value):
        self.enable_view(value)
        if self.channelConfig:
            mode = IMU_MODE_NORMAL
            orientation = kvFind(self, 'rcid', 'orientation')
            if not value:
                mode = IMU_MODE_DISABLED
            orientation.setFromValue(mode)
            self.channelConfig.mode = mode
            self.channelConfig.stale = True
            self.dispatch('on_modified')
            
    def on_config_updated(self, channelIndex, channelConfig, channelLabels):
        label = kvFind(self, 'rcid', 'label')
        label.text = channelLabels[channelIndex]

        enabled = kvFind(self, 'rcid', 'enabled')
        active = not channelConfig.mode == IMU_MODE_DISABLED
        self.enable_view(active)
        enabled.active = active
        
        orientation = kvFind(self, 'rcid', 'orientation')
        orientation.setFromValue(channelConfig.mode)

        mapping = kvFind(self, 'rcid', 'mapping')
        if channelIndex in(IMU_ACCEL_CHANNEL_IDS):
            mapping.setImuType('accel')
        elif channelIndex in(IMU_GYRO_CHANNEL_IDS):
            mapping.setImuType('gyro')

        mapping.setFromValue(channelConfig.chan)
        
            
        zeroValue = kvFind(self, 'rcid', 'zeroValue')
        zeroValue.text = str(channelConfig.zeroValue)
        self.channelConfig = channelConfig
        self.channelLabels = channelLabels
        
class ImuChannelsView(BaseConfigView):
    editors = []
    imu_cfg = None
    channelLabels = {0:'X', 1:'Y', 2:'Z', 3:'Yaw',4:'Pitch',5:'Roll',6:'Compass'}

    def __init__(self, **kwargs):
        Builder.load_file(IMU_CHANNELS_VIEW_KV)
        super(ImuChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')

        imu_container = self.ids.imu_channels
        self.appendImuChannels(imu_container, self.editors, IMU_ACCEL_CHANNEL_IDS)
        self.appendImuChannels(imu_container, self.editors, IMU_GYRO_CHANNEL_IDS)
        self.ids.sr.bind(on_sample_rate = self.on_sample_rate)
        
    def appendImuChannels(self, container, editors, ids):
        for i in ids:
            editor = ImuChannel(rcid='imu_chan_' + str(i))
            container.add_widget(editor)
            editor.bind(on_modified=self.on_modified)
            editors.append(editor)
    
    def on_calibrate(self):
        self.rc_api.calibrate_imu(self.on_calibrate_win, self.on_calibrate_fail)
        
    def on_calibrate_win(self, result):
        alertPopup('Calibration', 'Calibration Complete')
        
    def on_calibrate_fail(self, result):
        alertPopup('Calibration', 'Calibration Failed:\n\n' + str(result))
        
    def on_sample_rate(self, instance, value):
        if self.imu_cfg:
            for imuChannel in self.imu_cfg.channels:
                imuChannel.sampleRate = value
                imuChannel.stale = True
                self.dispatch('on_modified')
                
    def on_config_updated(self, rc_cfg):
        imu_cfg = rc_cfg.imuConfig
        channelCount = imu_cfg.channelCount

        common_sample_rate = 0
        for i in range(channelCount):
            imuChannel = imu_cfg.channels[i]
            editor = self.editors[i]
            editor.on_config_updated(i, imuChannel, self.channelLabels)
            common_sample_rate = imuChannel.sampleRate if common_sample_rate < imuChannel.sampleRate else common_sample_rate
        
        self.ids.sr.setValue(common_sample_rate, rc_cfg.capabilities.sample_rates.sensor)
        self.imu_cfg = imu_cfg

