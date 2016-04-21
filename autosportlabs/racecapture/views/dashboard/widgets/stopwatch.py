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
<PitstopTimerView>:
    exit_speed_frame: exit_speed_frame.__self__
    orientation: 'vertical'
    padding: (sp(10), sp(10))
    spacing: sp(10)
    FieldLabel:
        text: root.title
        halign: 'center'
        font_size: sp(50)
        size_hint_y: 0.15
    BoxLayout:
        id: exit_speed_frame_container
        size_hint_y: 0.7
        orientation: 'vertical'
        FieldLabel:
            canvas.before:
                Color:
                    rgba: ColorScheme.get_dark_background_translucent()
                Rectangle:
                    pos: self.pos
                    size: self.size
            id: timer
            shorten: False
            halign: 'center'
            valign: 'middle'
            max_lines: 1
            font_size: root.height * 0.38
            text: root.current_time
            on_texture: root.change_font_size()
        BoxLayout: 
            id: exit_speed_frame
            canvas.before:
                Color:
                    rgba: root.exit_speed_color
                Rectangle:
                    pos: self.pos
                    size: self.size
            padding: (sp(10), sp(10))
            orientation: 'horizontal'
            FieldLabel:
                id: exit_speed_label
                size_hint_x: 0.7
                shorten: False
                halign: 'left'
                max_lines: 1
                font_size: root.height * 0.2
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
                    font_size: root.height * 0.25
                    valign: 'middle'
                    text: root.exit_speed

    AnchorLayout:
        size_hint_y: 0.15
        IconButton:
            text: u'\uf00d'
            color: ColorScheme.get_primary()            
            on_release: root.dismiss()
'''

STOPWATCH_SPEED_CHANNEL = 'Speed'
STOPWATCH_CURRENT_LAP = 'CurrentLap'

STOPWATCH_NULL_TIME=''

class PitstopTimerView(BoxLayout):
    '''
    Provides a pit stop timer that automatically activates when certain speed
    thresholds are met. 
    '''
    _STOPWATCH_TICK = 0.1
    _FLASH_INTERVAL = 0.25
    _FLASH_COUNT = 10
    _EXIT_SPEED_CONTAINER_SIZE_HINT = 0.3
    _TIMER_WIDGET_SIZE_HINT = 0.4
    _SPEED_ALERT_THRESHOLD = 0.85
    _POPUP_SIZE_HINT = (0.75, 0.8)
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
    
    Builder.load_string(STOPWATCH_LAYOUT)
    
    def __init__(self, databus, title='Pit Stop', **kwargs):
        super(PitstopTimerView, self).__init__(**kwargs)
        self.title = title
        self.databus = databus
        self._popup = None
        self._current_time = 0.0
        self._flash_count = 0
        self._currently_racing = False
        databus.addChannelListener(STOPWATCH_SPEED_CHANNEL, self.set_speed)
        databus.addChannelListener(STOPWATCH_CURRENT_LAP, self.set_current_lap)
    
    def _set_exit_speed_frame_visible(self, visible):
        '''
        Shows or hides the frame containing the exit speed indicator
        :param visible true if exit speed frame should be visible
        :type visible
        '''
        container = self.ids.exit_speed_frame_container
        frame_visible = self.exit_speed_frame in container.children
        if visible:
            if not frame_visible:
                container.add_widget(self.exit_speed_frame)
        else:
            if frame_visible:
                container.remove_widget(self.exit_speed_frame)

    def _format_stopwatch_time(self):
        '''
        Format current laptime for display
        '''
        return format_laptime(self._current_time / 60.0)
        
    def _toggle_exit_speed_alert(self, alert_color):
        '''
        Toggles the background color for the exit speed frame
        '''
        if self.exit_speed_color == alert_color:
            self.exit_speed_color = ColorScheme.get_dark_background_translucent()
        else:
            self.exit_speed_color = alert_color
        
    def _update_speed_color(self):
        '''
        Selects the appropriate color for the exit speed indicator based on 
        configured speed threshold
        '''
        if self.current_speed > self.exit_speed_alert_threshold:
            self.ids.speed_rect.rect_color = ColorScheme.get_error()
            self._toggle_exit_speed_alert(ColorScheme.get_error())
        elif self.current_speed > self.exit_speed_alert_threshold * self._SPEED_ALERT_THRESHOLD:
            self.ids.speed_rect.rect_color = ColorScheme.get_alert()
            self.exit_speed_color = ColorScheme.get_dark_background_translucent()
        else:
            self.ids.speed_rect.rect_color = ColorScheme.get_happy()
            self.exit_speed_color = ColorScheme.get_dark_background_translucent()
        
    def _tick_stopwatch(self, *args):
        '''
        Increment the current stopwatch time
        '''
        self._current_time += self._STOPWATCH_TICK
        self.current_time = self._format_stopwatch_time()
        self.exit_speed = '{}'.format(int(self.current_speed))
        if self.current_speed > self.stop_threshold_speed:
            self._set_exit_speed_frame_visible(True)
        self._update_speed_color()

    def _stop_stopwatch(self):
        '''
        Stops the stopwatch timer
        '''
        Clock.unschedule(self._tick_stopwatch)
        self.current_time =  STOPWATCH_NULL_TIME

    def _in_race_mode(self):
        '''
        Return True if we think we're in 'racing mode'
        '''
        return self.current_speed > self.resume_threshold_speed and\
            self.current_lap > 0
            
    def _start_stopwatch(self):
        '''
        Starts the stopwatch timer
        '''
        if not self._popup:
            self._popup = ModalView(size_hint=self._POPUP_SIZE_HINT, auto_dismiss=False)
            self._popup.add_widget(self)
        self._set_exit_speed_frame_visible(False)
        self._popup.open()
        self._current_time = 0
        self._flash_count = 0
        self._currently_racing = False
        Clock.schedule_interval(self._tick_stopwatch, self._STOPWATCH_TICK)
    
    def _is_popup_open(self):
        '''
        Indicates if current popup is open
        :return True if popup is currently open
        '''
        return self._popup and self._popup._window is not None
        
    def _flash_pit_stop_time(self, *args):
        '''
        Flashes the final pit stop time when complete
        '''
        self.current_time = self._format_stopwatch_time() if self._flash_count % 2 == 0 else ''
        self._flash_count += 1
        if self._flash_count < self._FLASH_COUNT * 2:
            Clock.schedule_once(self._flash_pit_stop_time, self._FLASH_INTERVAL)
        else:
            self._popup.dismiss()
        
    def _finish_stopwatch(self):
        '''
        Finish the current stopwatch
        '''
        self._flash_count = 0
        self.ids.speed_rect.rect_color = ColorScheme.get_dark_background_translucent()
        self.exit_speed_color = ColorScheme.get_dark_background_translucent()
        self._set_exit_speed_frame_visible(False)        
        Clock.schedule_once(self._flash_pit_stop_time)
        self._stop_stopwatch()
        
    def check_popup(self):
        '''
        Check if we should pop-up the timer
        '''
        if self._in_race_mode():
            self._currently_racing = True
        if self.current_speed < self.stop_threshold_speed and\
                self._currently_racing and\
                not self._is_popup_open():
            self._start_stopwatch()
        
        if self.current_speed > self.resume_threshold_speed and\
                self._is_popup_open() and\
                self._flash_count == 0:
            self._finish_stopwatch()
            
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
        self._stop_stopwatch()
        
    def change_font_size(self):
        '''
        Auto resizes the timer widget if it spills over the edge of the bounding box
        '''
        widget = self.ids.timer
        try:
            if widget.texture_size[0] > widget.width:
                widget.font_size -= 1
        except Exception as e:
            Logger.warn('[PitstopTimerView] Failed to change font size: {}'.format(e))
