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
Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/tachometer.kv')


class LinearGauge(BoxLayout):
    # these values match the dimensions of the svg elements used in this gauge.

    value = NumericProperty(0)
    color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(LinearGauge, self).__init__(**kwargs)
        self.gauge_width = 2000
        self.gauge_height = 500
        x = self.pos[0]
        y = self.pos[1]

        scale_x = self.width / self.gauge_width
        scale_y = self.height / self.gauge_height

        with self.canvas:
            PushMatrix()
            self.dial_color = Color(rgba=self.color)
            self.gauge_translate = Translate(x, y, 0)
            self.gauge_scale = Scale(x=scale_x, y=scale_y)
            Rectangle(source='resource/gauge/horizontal_bar_gauge.png', pos=self.pos, size=(self.gauge_width, self.gauge_height))
            PopMatrix()
            PushMatrix()
            self.mask_translate = Translate(x, y, 0)
            self.mask_scale = Scale(x=scale_x, y=scale_y)
            Rectangle(source='resource/gauge/horizontal_bar_gauge_mask.png', pos=self.pos, size=(self.gauge_width, self.gauge_height))
            PopMatrix()

        with self.canvas.after:
            PushMatrix()
            Color(1, 1, 1, 1)
            self.shadow_translate = Translate(x, y, 0)
            self.shadow_scale = Scale(x=scale_x, y=scale_y)
            Rectangle(source='resource/gauge/horizontal_bar_gauge_shadow.png', pos=self.pos, size=(self.gauge_width, self.gauge_height))
            PopMatrix()

        self.bind(pos=self.update_all, size=self.update_all)

    def update_all(self, *args):
        x = self.pos[0]
        y = self.pos[1]
        self.gauge_translate.x = x
        self.gauge_translate.y = y
        self.shadow_translate.x = x
        self.shadow_translate.y = y
        self.mask_translate.x = x
        self.mask_translate.y = y

        scale_x = self.width / self.gauge_width
        scale_y = self.height / self.gauge_height
        self.gauge_scale.x = scale_x
        self.gauge_scale.y = scale_y
        self.shadow_scale.x = scale_x
        self.shadow_scale.y = scale_y
        self.mask_scale.x = scale_x
        self.mask_scale.y = scale_y

    def on_value(self, instance, value):
        x = self.pos[0]
        y = self.pos[1]
        offset = (value / 100.0) * self.width
        self.mask_translate.x = x + offset

    def on_color(self, instance, value):
        self.dial_color.rgba = value

class TachometerGauge(CustomizableGauge):

    def __init__(self, **kwargs):
        super(TachometerGauge, self).__init__(**kwargs)
        self.initWidgets()

    def initWidgets(self):
        pass

    def on_channel(self, instance, value):
        addChannelView = self.ids.get('add_gauge')
        if addChannelView: addChannelView.text = '+' if value == None else ''
        return super(TachometerGauge, self).on_channel(instance, value)


    def update_colors(self):
        self.ids.gauge.color = self.select_alert_color()
        return super(TachometerGauge, self).update_colors()

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
            Logger.error('TachometerGauge: error setting gauge value ' + str(e))

        return super(TachometerGauge, self).on_value(instance, value)

