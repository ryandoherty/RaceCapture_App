import kivy
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.logger import Logger
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from iconbutton import RoundedRect
from autosportlabs.racecapture.theme.color import ColorScheme

STOPWATCH_LAYOUT='''
<StopwatchView>:
    orientation: 'vertical'
    padding: (sp(10), sp(10))
    spacing: sp(10)
    FieldLabel:
        text: root.title
        halign: 'center'
        font_size: sp(50)
        size_hint_y: 0.1
    BoxLayout:
        canvas.before:
            Color:
                rgba: ColorScheme.get_dark_background_translucent()
            Rectangle:
                pos: self.pos
                size: self.size
        size_hint_y: 0.4
        FieldLabel:
            id: timer
            shorten: False
            halign: 'center'
            valign: 'middle'
            max_lines: 1
            font_size: sp(150)
            text: root.current_time
            on_texture: root.change_font_size()
    BoxLayout:
        padding: (sp(10), sp(10))
        canvas.before:
            Color:
                rgba: root.exit_speed_color
            Rectangle:
                pos: self.pos
                size: self.size
        size_hint_y: 0.3
        orientation: 'horizontal'
        FieldLabel:
            size_hint_x: 0.7
            shorten: False
            halign: 'left'
            max_lines: 1
            font_size: sp(80)
            text: 'Exit Speed'
            valign: 'middle'
            
        AnchorLayout:
            size_hint_x: 0.3
            RoundedRect:
                rect_color: ColorScheme.get_happy()
                id: speed_rect        
            FieldLabel:        
                id: speed
                shorten: False
                halign: 'center'
                max_lines: 1
                font_size: sp(100)
                valign: 'middle'
                text: root.exit_speed

    AnchorLayout:
        size_hint_y: 0.2
        IconButton:
            text: u'\uf00d'
            color: ColorScheme.get_primary()            
            on_release: root.dismiss()
'''

STOPWATCH_SPEED_CHANNEL = 'Speed'
STOPWATCH_CURRENT_LAP = 'CurrentLap'
STOPWATCH_TICK = 0.1
STOPWATCH_NULL_TIME=''

class StopwatchView(BoxLayout):
    #Settings
    stop_threshold_speed = NumericProperty(2.0)
    resume_threshold_speed = NumericProperty(55.0)
    exit_speed_alert_threshold = NumericProperty(35.0)
    
    exit_speed_color = ListProperty(ColorScheme.get_dark_background_translucent())
    title = StringProperty('')
    current_time = StringProperty(STOPWATCH_NULL_TIME)
    exit_speed = StringProperty('')
    current_speed = NumericProperty(None)
    current_lap = NumericProperty(None)
    last_triggered_lap = NumericProperty(None)
    
    Builder.load_string(STOPWATCH_LAYOUT)
    
    def __init__(self, databus, title='Pit Stop', **kwargs):
        super(StopwatchView, self).__init__(**kwargs)
        self.title = title
        self.databus = databus
        self._popup = None
        self._current_time = 0.0
        databus.addChannelListener(STOPWATCH_SPEED_CHANNEL, self.set_speed)
        databus.addChannelListener(STOPWATCH_CURRENT_LAP, self.set_current_lap)
    
    def _tick_stopwatch(self, *args):
        self._current_time += STOPWATCH_TICK
        self.current_time = format_laptime(self._current_time / 60.0)
        self.exit_speed = '{}'.format(int(self.current_speed))
        self.update_colors()
        
    def _toggle_exit_speed_alert(self, alert_color):
        if self.exit_speed_color == alert_color:
            self.exit_speed_color = ColorScheme.get_dark_background_translucent()
        else:
            self.exit_speed_color = alert_color
        
    def update_colors(self):
        if self.current_speed > self.exit_speed_alert_threshold:
            self.ids.speed_rect.rect_color = ColorScheme.get_error()
            self._toggle_exit_speed_alert(ColorScheme.get_error())
        elif self.current_speed > self.exit_speed_alert_threshold * 0.75:
            self.ids.speed_rect.rect_color = ColorScheme.get_alert()
            self.ids.speed_rect.rect_color = ColorScheme.get_alert()
            self.exit_speed_color = ColorScheme.get_dark_background_translucent()
        else:
            self.ids.speed_rect.rect_color = ColorScheme.get_happy()
            self.exit_speed_color = ColorScheme.get_dark_background_translucent()
        
    def _start_timer(self):
        self._current_time = 0
        Clock.schedule_interval(self._tick_stopwatch, STOPWATCH_TICK)
    
    def _stop_timer(self):
        Clock.unschedule(self._tick_stopwatch)
        self.current_time =  STOPWATCH_NULL_TIME

    def _start_stopwatch(self):
        if not self._popup:
            self._popup = ModalView(size_hint=(0.75, 0.8), auto_dismiss=False)
            self._popup.add_widget(self)
        self._popup.open()
        self.last_triggered_lap = self.current_lap
        self._start_timer()
    
    def _is_popup_open(self):
        return self._popup and self._popup._window is not None
        
    def _cancel_stopwatch(self):
        self._popup.dismiss()
        self._stop_timer()
        
    def check_popup(self):
        if self.current_speed < self.stop_threshold_speed and\
                self.current_lap > 0 and\
                self.last_triggered_lap != self.current_lap and\
                not self._is_popup_open():
            self._start_stopwatch()
        
        if self.current_speed > self.resume_threshold_speed and\
                self._is_popup_open():
            self._cancel_stopwatch()
            
    def on_current_speed(self, instance, value):
        self.check_popup()
    
    def on_current_lap(self, instance, value):
        self.check_popup()

    def set_speed(self, value):
        self.current_speed = value
    
    def set_current_lap(self, value):
        self.current_lap = value

    def dismiss(self):
        self._popup.dismiss()
        self._stop_timer()
        
    def change_font_size(self):
        widget = self.ids.timer
        try:
            if widget.texture_size[0] > widget.width:
                widget.font_size -= 1
        except Exception as e:
            Logger.warn('[StopwatchView] Failed to change font size: {}'.format(e))
