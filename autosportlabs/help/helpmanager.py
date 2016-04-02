import kivy
kivy.require('1.9.1')
from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble
from autosportlabs.racecapture.theme.color import ColorScheme
from __builtin__ import staticmethod
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger
from kivy.metrics import sp
from kivy.app import Builder
import json
import os
import traceback

__all__ = ('check_help_popup_popup')

HELP_INFO_LAYOUT='''
<HelpInfo>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: ColorScheme.get_dark_background()
        Rectangle:
            pos: self.pos
            size: self.size
    padding: (sp(10), sp(10))
    Label:
        text: root.title_text
        font_name: 'resource/fonts/ASL_light.ttf'
        font_size: self.height * 0.8
        size_hint_y: 0.15
    Label:
        size_hint_y: 0.65
        font_name: 'resource/fonts/ASL_light.ttf'
        text: root.help_text
        #size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]
    AnchorLayout:
        size_hint_y: 0.2
        LabelIconButton:
            id: ok
            title: 'Got It'
            tile_color: ColorScheme.get_secondary_text()
            icon_size: self.height * 0.5
            title_font_size: self.height * 0.7
            icon: u'\uf00c'
            size_hint_x: 0.25
            on_press: root.on_ok()

<HelpBubble>:
    arrow_image: 'autosportlabs/help/help_arrow.png'
'''

class HelpBubble(CenteredBubble):
    pass
    
class HelpInfo(BoxLayout):
    '''
    Displays a help popup message with a title and description
    
    Description:
    The help popup is designed to be a 'show once only / first time user's help'. The help function can be repeatedly called;
    the caller does not need to manage if the help has been shown already.

    The HelpInfo system pulls messages from a central help resource file (resource/help/help_text.json).
    Each help message is referenced by it's respective key, identified in the file.
    
    A popup help bubble can be requested with the specified message key. The bubble is centered on the specified widget. 
    An arrow can be specified to point towards something of interest.
    
    Usage:
    * Create an entry in the resource/help/help_text.json file
    * To display the help message, call help_popup(<help_key>, <widget_to_center_on>, <arrow_position>):
    ** The value for <arrow_position> are the same as specified by kivy Bubble.
    '''
    Builder.load_string(HELP_INFO_LAYOUT)
    HELP_POPUP_TIMEOUT = 30.01
    HELP_POPUP_SIZE = (sp(500), sp(200))
    settings = None
    loaded = False
    help_info = {}
    title_text = StringProperty('')
    help_text = StringProperty('')
    
    def __init__(self, key, **kwargs):
        super(HelpInfo,self).__init__(**kwargs)
        self._key = key 

    @staticmethod
    def get_helptext(key):
        if HelpInfo.loaded == False:
            help_json = open(os.path.join(HelpInfo.settings.base_dir, 'resource', 'help', 'help_text.json'))
            HelpInfo.help_info = json.load(help_json)
            Logger.info('HelpInfo: Loaded help text')

        helptext = HelpInfo.help_info.get(key, None)
        if not helptext:
            Logger.error('HelpInfo: Could not load help for key {}'.format(key))
        return helptext
        
    @staticmethod
    def help_popup(key, widget, arrow_pos='bottom_mid'):
        '''
        Display a help popup message. This message will only show once (first time help for users) 
        
        Args:
            key: the key representing the help text
            widget: the widget to center on
            arrow_pos: help arrow position, as defined in kivy Bubble widget.
        '''
        try:
            settings = HelpInfo.settings
            show_help = settings.userPrefs.get_pref('help', key, True)
            if show_help == True:
                helptext = HelpInfo.get_helptext(key)
                if helptext:
                    content = HelpInfo(key, title_text=helptext['title'], help_text=helptext['text'])
                    help_popup = HelpBubble(arrow_pos = arrow_pos,
                                            size=HelpInfo.HELP_POPUP_SIZE,
                                            size_hint = (None,None))
                    help_popup.add_widget(content)
                    help_popup.auto_dismiss_timeout(HelpInfo.HELP_POPUP_TIMEOUT)
                    widget.get_root_window().add_widget(help_popup)
                    help_popup.center_on(widget)
        except Exception as e:
            Logger.critical('HelpInfo: Failed to show help popup: {} {}'.format(e, traceback.format_exc()))

    def on_ok(self):
        HelpInfo.settings.userPrefs.set_pref('help', self._key, False)
        self.parent.parent.dismiss()
