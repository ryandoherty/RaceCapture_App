import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout


class BaseConfigView(BoxLayout):
    def __init__(self, **kwargs):    
        super(BaseConfigView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_modified')
        self.register_event_type('on_config_modified')
        
    def on_modified(self, *args):
        self.dispatch('on_config_modified', *args)
    
    def on_config_modified(self, *args):
        pass
    
    def on_tracks_updated(self, trackmanager):
        pass

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