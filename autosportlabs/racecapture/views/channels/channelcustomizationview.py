import kivy
kivy.require('1.9.0')
from iconbutton import IconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from autosportlabs.uix.textwidget import TextWidget
from kivy.uix.slider import Slider
from utils import kvFind
from autosportlabs.racecapture.views.color.colorpickerview import ColorBlock
from autosportlabs.racecapture.settings.prefs import Range
from autosportlabs.racecapture.views.color.colorpickerview import ColorPickerView

Builder.load_file('autosportlabs/racecapture/views/channels/channelcustomizationview.kv')

class RangeLabel(TextWidget):
    pass

class ChannelCustomizationView(FloatLayout):
    
    _popup = None
    def __init__(self, **kwargs):
        self.settings = None
        self.channel = None
        self.channelMeta = None
        self.warnRange = Range()
        self.alertRange = Range()
        self.valueFormat = '{0:.0f}'

        super(ChannelCustomizationView, self).__init__(**kwargs)
        self.register_event_type('on_channel_customization_close')
        
        self.settings = kwargs.get('settings')
        self.channel = kwargs.get('channel')
        self.channelMeta = self.settings.runtimeChannels.findChannelMeta(self.channel)
        self.init_view()
        
    
    def getWarnPrefsKey(self, channel):
        return '{}.warn'.format(self.channel)
    
    def getAlertPrefsKey(self, channel):
        return '{}.alert'.format(self.channel)
        
    def on_close(self):
        self.settings.userPrefs.set_range_alert(self.getWarnPrefsKey(self.channel), self.warnRange)
        self.settings.userPrefs.set_range_alert(self.getAlertPrefsKey(self.channel), self.alertRange)
        self.dispatch('on_channel_customization_close', self.warnRange, self.alertRange)

    def on_channel_customization_close(self, instance, *args):
        pass
    
    def setupSlider(self, slider, channelMeta, initialValue):
        min = channelMeta.min
        max = channelMeta.max
        
        slider.value = initialValue if initialValue != None else min
        slider.min = min
        slider.max = max
        slider.step = (max - min) / 100
        
    def sanitize_range(self, channel_range, channel_meta):
        channel_range.min = channel_meta.min if channel_range.min < channel_meta.min else channel_range.min
        channel_range.max = channel_meta.max if channel_range.max > channel_meta.max else channel_range.max
        
    def init_view(self):
        channel = self.channel
        channelMeta = self.channelMeta
        if channel and channelMeta:
            self.valueFormat = '{0:.' + str(self.channelMeta.precision) + 'f}'        
            
            warnRange = self.settings.userPrefs.get_range_alert(self.getWarnPrefsKey(channel), 
                    Range(min=channelMeta.max, max=channelMeta.max, color=Range.DEFAULT_WARN_COLOR))
            alertRange = self.settings.userPrefs.get_range_alert(self.getAlertPrefsKey(channel), 
                    Range(min=channelMeta.max, max=channelMeta.max, color=Range.DEFAULT_ALERT_COLOR))

            self.sanitize_range(warnRange, channelMeta)
            self.sanitize_range(alertRange, channelMeta)
            
            self.setupSlider(self.ids.warnLowSlider, channelMeta, warnRange.min)
            self.setupSlider(self.ids.warnHighSlider, channelMeta, warnRange.max)
            
            self.setupSlider(self.ids.alertLowSlider, channelMeta, alertRange.min)
            self.setupSlider(self.ids.alertHighSlider, channelMeta, alertRange.max)
            
            self.ids.selectedWarnColor.color = warnRange.color
            self.ids.selectedAlertColor.color = alertRange.color
            
            self.alertRange = alertRange
            self.warnRange = warnRange
        
    def _synchLabels(self, gaugeRange, lowSlider, highSlider, lowLabel, highLabel):
        min_range = gaugeRange.min if gaugeRange.min != None else self.channelMeta.min
#        if min_range: 
        lowLabel.text = self.valueFormat.format(min_range)
        lowSlider.value = min_range

        max_range = gaugeRange.max if gaugeRange.max != None else self.channelMeta.max
#        if max_range:
        highLabel.text = self.valueFormat.format(max_range)
        highSlider.value = max_range

    def _updateHighRange(self, gaugeRange, lowSlider, highSlider, lowLabel, highLabel, value):
        gaugeRange.max = value
        if gaugeRange.min == None: gaugeRange.min = self.channelMeta.min
        if value < gaugeRange.min:
            gaugeRange.min = value
        self._synchLabels(gaugeRange, lowSlider, highSlider, lowLabel, highLabel)
                
    def _updateLowRange(self, gaugeRange, lowSlider, highSlider, lowLabel, highLabel, value):
        gaugeRange.min = value
        if gaugeRange.max == None: gaugeRange.max = self.channelMeta.min
        if value > gaugeRange.max:
            gaugeRange.max = value
        self._synchLabels(gaugeRange, lowSlider, highSlider, lowLabel, highLabel)
    
    def on_alertHigh(self, instance, value):
        self._updateHighRange(self.alertRange, self.ids.alertLowSlider, self.ids.alertHighSlider, self.ids.alertLowValue, self.ids.alertHighValue, value)
    
    def on_alertLow(self, instance, value):
        self._updateLowRange(self.alertRange, self.ids.alertLowSlider, self.ids.alertHighSlider, self.ids.alertLowValue, self.ids.alertHighValue, value)
    
    def on_warnHigh(self, instance, value):
        self._updateHighRange(self.warnRange, self.ids.warnLowSlider, self.ids.warnHighSlider, self.ids.warnLowValue, self.ids.warnHighValue, value)        

    def on_warnLow(self, instance, value):
        self._updateLowRange(self.warnRange, self.ids.warnLowSlider, self.ids.warnHighSlider, self.ids.warnLowValue, self.ids.warnHighValue, value)
        
    def popup_dismissed(self, *args):
        self._popup = None
        
    def dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None
        
    def warnColorSelected(self, instance, value):
        self.warnRange.color = value
        self.ids.selectedWarnColor.color = value
        self.dismiss_popup()

    def alertColorSelected(self, instance, value):
        self.alertRange.color = value
        self.ids.selectedAlertColor.color = value
        self.dismiss_popup()
        
    def show_color_select_popup(self, title, content):
        popup = Popup(title="Warning Color", content=content, size_hint=(0.4, 0.6))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
            
    def on_warn_color(self):
        content = ColorPickerView(color=self.warnRange.color)
        content.bind(on_color_selected=self.warnColorSelected)
        content.bind(on_color_cancel=self.dismiss_popup)
        self.show_color_select_popup('Warning Color', content)
        
    def on_alert_color(self):
        content = ColorPickerView(color=self.alertRange.color)
        content.bind(on_color_selected=self.alertColorSelected)
        content.bind(on_color_cancel=self.dismiss_popup)
        self.show_color_select_popup('Alert Color', content)
