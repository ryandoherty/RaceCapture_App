import kivy
kivy.require('1.8.0')
from iconbutton import IconButton
from kivy.app import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from fieldlabel import FieldLabel
from kivy.uix.slider import Slider
from utils import kvFind
from autosportlabs.racecapture.settings.prefs import Range

Builder.load_file('autosportlabs/racecapture/views/channels/channelcustomizationview.kv')

class ChannelCustomizationView(FloatLayout):
    def __init__(self, **kwargs):
        self.settings = None
        self.channel = None
        super(ChannelCustomizationView, self).__init__(**kwargs)
        self.register_event_type('on_channel_customization_close')
        
        self.settings = kwargs.get('settings')
        self.channel = kwargs.get('channel')
        self.initView()
        
    
    def on_close(self):
        self.dispatch('on_channel_customization_close')
        pass

    def on_channel_customization_close(self):
        pass
    
    def setupSlider(self, slider, channelMeta, initialValue):
        min = channelMeta.min
        max = channelMeta.max
        slider.value = initialValue
        slider.min = min
        slider.max = max
        slider.step = (max - min) / 100
        
    def initView(self):
        channel = self.channel
        if channel:
            channelMeta = self.settings.systemChannels.findChannelMeta(channel)
            warnRange = self.settings.userPrefs.getRangeAlert('{}.warn'.format(self.channel))
            if not warnRange: warnRange = Range(low=channelMeta.low, high=channelMeta.high)
            
            alertRange = self.settings.userPrefs.getRangeAlert('{}.alert', format(self.channel))
            if not alertRange: alertRange = Range(low=channelMeta.low, high=channelMeta.high)
            
            warnLowSlider = kvFind(self, 'id', 'warnLow')
            self.setupSlider(warnLowSlider, channelMeta, warnRange.min)

            warnHighSlider = kvFind(self, 'id', 'warnHigh')
            self.setupSlider(warnHighSlider, channelMeta, warnRange.max)
            
            alertLowSlider = kvFind(self, 'id', 'alertLow')
            self.setupSlider(alertLowSlider, channelMeta, alertRange.min)
            
            alertHighSlider = kvFind(self, 'id', 'alertHigh')
            self.setupSlider(alertHighSlider, channelMeta, alertRange.max)
            