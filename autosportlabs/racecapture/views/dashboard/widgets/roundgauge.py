import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.metrics import dp
from autosportlabs.racecapture.views.dashboard.widgets.gauge import CustomizableGauge
from utils import kvFind
from kivy.graphics import *
from kivy.properties import NumericProperty, ListProperty
from kivy.logger import Logger
Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/roundgauge.kv')


class SweepGauge(BoxLayout):
    # these values match the dimensions of the svg elements used in this gauge.

    value = NumericProperty(0)
    color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(SweepGauge, self).__init__(**kwargs)
        self.gauge_height = 110
        self.gauge_width = 100
        self.zoom_factor = 1.1

        self.mask_rotations = []
        size = self.height if self.height < self.width else self.width
        gauge_height = size / self.gauge_height
        x_center = self.pos[0] + self.width / 2 - self.gauge_width / 2
        y_center = self.pos[1] + self.height / 2 - self.gauge_height / 2

        with self.canvas:
            PushMatrix()
            self.dial_color = Color(rgba=self.color)
            self.gauge_translate = Translate(x_center, y_center, 0)
            self.gauge_scale = Scale(x=gauge_height, y=gauge_height)
            Rectangle(source='resource/gauge/round_gauge_270.png', pos=self.pos, size=self.size)
            PushMatrix()
            self.mask_rotations.append(Rotate(angle=-135, axis=(0, 0, 1), origin=(self.center[0], self.center[1])))
            Rectangle(source='resource/gauge/gauge_mask.png')
            PopMatrix()
            PushMatrix()
            self.mask_rotations.append(Rotate(angle=-225, axis=(0, 0, 1), origin=(self.center[0], self.center[1])))
            Rectangle(source='resource/gauge/gauge_mask.png')
            PopMatrix()
            PushMatrix()
            self.mask_rotations.append(Rotate(angle=-315, axis=(0, 0, 1), origin=(self.center[0], self.center[1])))
            Rectangle(source='resource/gauge/gauge_mask.png')
            PopMatrix()
            PopMatrix()

        with self.canvas.after:
            PushMatrix()
            Color(1, 1, 1, 1)
            self.shadow_translate = Translate(x_center, y_center, 0)
            self.shadow_scale = Scale(x=gauge_height, y=gauge_height)
            Rectangle(source='resource/gauge/round_gauge_270_shadow.png')
            PopMatrix()

        self.bind(pos=self.update_all, size=self.update_all)

    def update_all(self, *args):
        size = self.height if self.height < self.width else self.width
        gauge_height = size / self.gauge_height * self.zoom_factor

        x_center = self.pos[0] + self.width / 2 - (self.gauge_width / 2) * gauge_height
        y_center = self.pos[1] + self.height / 2 - (self.gauge_height / 2) * gauge_height

        self.gauge_translate.x = x_center
        self.gauge_translate.y = y_center
        self.shadow_translate.x = x_center
        self.shadow_translate.y = y_center

        self.gauge_scale.x = gauge_height
        self.gauge_scale.y = gauge_height
        self.shadow_scale.x = gauge_height
        self.shadow_scale.y = gauge_height

    def on_value(self, instance, value):
        angle = (value * 270) / 100
        self.mask_rotations[0].angle = -135 - angle
        self.mask_rotations[1].angle = -135 - angle  if angle > 90 else -225
        self.mask_rotations[2].angle = -135 - angle  if angle > 180 else -315

    def on_color(self, instance, value):
        self.dial_color.rgba = value

class RoundGauge(CustomizableGauge):

    def __init__(self, **kwargs):
        super(RoundGauge, self).__init__(**kwargs)
        self.initWidgets()

    def initWidgets(self):
        pass

    def on_channel(self, instance, value):
        addChannelView = self.ids.get('add_gauge')
        if addChannelView: addChannelView.text = '+' if value == None else ''
        return super(RoundGauge, self).on_channel(instance, value)


    def update_colors(self):
        self.ids.gauge.color = self.select_alert_color()
        return super(RoundGauge, self).update_colors()

    def on_value(self, instance, value):
        try:
            value = self.value
            min = self.min
            max = self.max
            railedValue = value
            if railedValue > max:
                railedValue = max
            if railedValue < min:
                railedValue = min

            range = max - min
            offset = railedValue - min
            self.ids.gauge.value = offset * 100 / range
        except Exception as e:
            Logger.error('RoundGauge: error setting gauge value ' + str(e))

        return super(RoundGauge, self).on_value(instance, value)

