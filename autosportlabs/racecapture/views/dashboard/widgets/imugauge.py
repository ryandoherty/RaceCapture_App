import kivy
kivy.require('1.9.1')
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind, kvquery
from kivy.properties import NumericProperty, ObjectProperty
from autosportlabs.uix.imu.imuview import ImuView
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/imugauge.kv')

class ImuGauge(Gauge):
    GYRO_SCALING = 0.1
    ACCEL_X = "AccelX"
    ACCEL_Y = "AccelY"
    ACCEL_Z = "AccelZ"
    GYRO_YAW = "Yaw"
    GYRO_PITCH = "Pitch"
    GYRO_ROLL = "Roll"
    
    channel_metas = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super(ImuGauge, self).__init__(**kwargs)
    
    def on_channel_meta(self, channel_metas):
        self.channel_meta = channel_metas
                        
    def on_data_bus(self, instance, value):
        self._update_channel_binding()
    
    def update_colors(self):
        view = self.valueView
        if view:
            view.color = self.normal_color

    def refresh_value(self, value):
        view = self.valueView
        if view:
            view.text = self.value_formatter(value)
            self.update_colors()
        
    def on_value(self, instance, value):
        self.refresh_value(value)

    def sensor_formatter(self, value):
        return "" if value is None else self.sensor_format.format(value)
    
    def on_channel(self, instance, value):
        self._update_gauge_meta()
                
    def _update_channel_binding(self):
        dataBus = self.data_bus
        if dataBus:
            dataBus.addChannelListener(self.ACCEL_X, self.set_accel_x)
            dataBus.addChannelListener(self.ACCEL_Y, self.set_accel_y)
            dataBus.addChannelListener(self.ACCEL_Z, self.set_accel_z)
            dataBus.addChannelListener(self.GYRO_YAW, self.set_gyro_yaw)
            dataBus.addChannelListener(self.GYRO_PITCH, self.set_gyro_pitch)
            dataBus.addChannelListener(self.GYRO_ROLL, self.set_gyro_roll)
            dataBus.addMetaListener(self.on_channel_meta)

    def set_accel_x(self, value):
        self.ids.imu.accel_x = value
        
    def set_accel_y(self, value):
        self.ids.imu.accel_y = value        
        
    def set_accel_z(self, value):
        self.ids.imu.accel_z = value
                
    def set_gyro_yaw(self, value):
        self.ids.imu.gyro_yaw = value * self.GYRO_SCALING
                
    def set_gyro_pitch(self, value):
        self.ids.imu.gyro_pitch = value  * self.GYRO_SCALING
                
    def set_gyro_roll(self, value):                
        self.ids.imu.gyro_roll = value  * self.GYRO_SCALING
        