import time
import kivy
kivy.require('1.9.1')

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.accordion import Accordion, AccordionItem
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from kivy.metrics import dp
from utils import *

class BaseChannelView(BoxLayout):
    channelConfig = None
    channels = None
    def __init__(self, **kwargs):
        super(BaseChannelView, self).__init__(**kwargs)
        self.ids.sr.bind(on_sample_rate = self.on_sample_rate)
        channel_selector=self.ids.chan_id
        self.channels = kwargs.get('channels')
        channel_selector.bind(on_channel = self.on_channel)
        channel_selector.dispatch('on_channels_updated', self.channels)
        self.register_event_type('on_modified')
    
    def on_modified(self, channelConfig):
        pass
    
    def on_channel(self, *args):
        if self.channelConfig:
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)

    def on_sample_rate(self, instance, value):
        if self.channelConfig:
            self.channelConfig.sampleRate = value
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)

        
class BaseConfigView(BoxLayout):
    channels = None
    rc_api = None
    def __init__(self, **kwargs):    
        super(BaseConfigView, self).__init__(**kwargs)
        self.rc_api = kwargs.get('rc_api')
        self.channels = kwargs.get('channels')
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_modified')
        self.register_event_type('on_config_modified')
        
    def on_modified(self, *args):
        self.dispatch('on_config_modified', *args)
    
    def on_config_modified(self, *args):
        pass
    
    def on_tracks_updated(self, track_manager):
        pass
        

class LazyloadAccordionItem(AccordionItem):
    def __init__(self, max_sample_rate, builder, channel_index, **kwargs):
        super(LazyloadAccordionItem, self).__init__(**kwargs)
        self.max_sample_rate = max_sample_rate
        self.lazy_builder = builder
        self.channel_index = channel_index
        self.loaded = False
        self.editor = None
        
    def on_collapse(self, instance, value):
        super(LazyloadAccordionItem, self).on_collapse(instance, value)
        if value == False and self.loaded == False:
                editor = self.lazy_builder(self.channel_index, self.max_sample_rate)
                self.add_widget(editor)
                self.loaded = True
                self.editor = editor

class BaseMultiChannelConfigView(BaseConfigView):
    config = None
    channel_title = 'Channel '
    accordion_item_height = 100
    
    _accordion = None
    _channel_count = 0
    _channel_editors = []
    
    def __init__(self, **kwargs):    
        super(BaseMultiChannelConfigView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')        
        accordion = Accordion(orientation='vertical', size_hint=(1.0, None))        
        sv = ScrollContainer(size_hint=(1.0,1.0), do_scroll_x=False)
        sv.add_widget(accordion)
        self._accordion = accordion
        self.add_widget(sv)
        
    def update_channel_editors(self, channel_count, max_sample_rate):
        accordion = self._accordion
        if self._channel_count != channel_count:
            self._channel_editors = []
            accordion.height = self.accordion_item_height * channel_count
            title = self.channel_title
            for i in range(channel_count):
                channel = LazyloadAccordionItem(title=title + str(i + 1), builder=self.channel_builder, channel_index=i, max_sample_rate=max_sample_rate)
                accordion.add_widget(channel)
                self._channel_editors.append(channel)
            self._channel_count = channel_count
            

    def on_config_updated(self, rc_cfg):
        config = self.get_specific_config(rc_cfg)
        max_sample_rate = rc_cfg.capabilities.sample_rates.sensor
        channel_count = len(config.channels)
        self.update_channel_editors(channel_count, max_sample_rate)
        accordion = self._accordion
        for i in range(channel_count):
            channel_config = config.channels[i]
            accordion_item = self._channel_editors[i]
            if accordion_item.editor is not None:
                accordion_item.editor.on_config_updated(channel_config, max_sample_rate)
            
            self.setAccordionItemTitle(accordion, config.channels, channel_config)

        self.config = config
        
    def on_modified(self, instance, channel_config):
        self.setAccordionItemTitle(self._accordion, self.config.channels, channel_config)
        super(BaseMultiChannelConfigView, self).on_modified(self, instance, channel_config)

    def setAccordionItemTitle(self, accordion, channel_configs, config):
            i = channel_configs.index(config)
            accordion_children = accordion.children
            accordion_item = accordion_children[len(accordion_children) - i - 1]
            accordion_item.title = self.createTitleForChannel(config)
        
    def createTitleForChannel(self, channel_config):
        try:
            sample_rate = channel_config.sampleRate
            sample_rate_info = 'Disabled' if sample_rate == 0 else (str(sample_rate) + 'Hz')
            return '{} ({})'.format(channel_config.name, sample_rate_info)
        except:
            return 'Unknown Channel'
