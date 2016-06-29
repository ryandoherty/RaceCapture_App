import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from autosportlabs.racecapture.views.dashboard.widgets.gauge import CustomizableGauge
from kivy.graphics import Rectangle, PushMatrix, PopMatrix, Color, Scale, Translate
from kivy.properties import NumericProperty, ListProperty
from kivy.logger import Logger

class LinearGauge(BoxLayout):
    '''
    A widget that displays a horizontal, triangular shaped bar graph style gauge.
    '''

    value = NumericProperty(0)
    color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super(LinearGauge, self).__init__(**kwargs)
        # these values match the actual dimensions of the referenced graphic assets
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
        '''
        Update all positions and sizes for graphics in widgets.
        '''
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
        '''
        Translate a 0-100 value to a 0-100% gauge value
        :param instance the widget instance
        :type instance Widget
        :param value the value of the widget
        :type value float
        '''
        x = self.pos[0]
        y = self.pos[1]
        offset = (value / 100.0) * self.width
        self.mask_translate.x = x + offset

    def on_color(self, instance, value):
        '''
        :param instance the widget instance
        :type instance Widget
        :param value the color value
        :type value list
        '''
        self.dial_color.rgba = value


class TachometerGauge(CustomizableGauge):
    Builder.load_string("""
<TachometerGauge>:
    anchor_x: 'center'
    anchor_y: 'center'
    value_size: self.height * 0.3
    title_size: self.height * 0.15
    LinearGauge:
        id: gauge
    AnchorLayout:
        anchor_x: 'left'
        anchor_y: 'center'
        BoxLayout:
            orientation: 'vertical'
            BoxLayout:
                size_hint_y: 0.4
            BoxLayout:
                size_hint_y: 0.4
                orientation: 'vertical'
                FieldLabel:
                    size_hint_y: 0.6
                    id: value
                    font_size: root.value_size
                    halign: 'left'
                    valign: 'bottom'
                FieldLabel:
                    size_hint_y: 0.4
                    id: title
                    halign: 'left'
                    valign: 'bottom'
                    font_size: root.title_size
            BoxLayout:
                size_hint_y: 0.2
    """)

    def __init__(self, **kwargs):
        super(TachometerGauge, self).__init__(**kwargs)

    def update_colors(self):
        '''
        Refreshes the color of the gauge
        '''
        self.ids.gauge.color = self.select_alert_color()
        return super(TachometerGauge, self).update_colors()

    def update_title(self, channel, channel_meta):
        '''
        Override the default title setter to prevent units from being shown
        as this is a concise label (like the DigitalGauge)
        '''
        self.title = channel if channel else ''

    def on_value(self, instance, value):
        '''
        Set the value of the gauge.
        Limit the value to the max value of the widget so it shows only 0-100%
        :param instance the widget instance
        :type instance Widget
        :param value the value of the widget
        :type value float
        '''
        try:
            value = self.value
            min_value = self.min
            max_value = self.max
            railed_value = value
            if railed_value > max_value:
                railed_value = max_value
            if railed_value < min_value:
                railed_value = min_value

            value_range = max_value - min_value
            offset = railed_value - min_value
            self.ids.gauge.value = offset * 100 / value_range
        except Exception as e:
            # Only log error vs potentially flooding crash handler
            Logger.error('TachometerGauge: error setting gauge value {}'.format(e))

        return super(TachometerGauge, self).on_value(instance, value)

