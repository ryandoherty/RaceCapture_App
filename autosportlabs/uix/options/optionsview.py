#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, SwapTransition
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.theme.color import ColorScheme
from iconbutton import IconButton


class BaseOptionsScreen(Screen):
    '''
    A base class for a customization screen. This can be extended when adding the next option screen
    '''
    def __init__(self, params, values, **kwargs):
        super(BaseOptionsScreen, self).__init__(**kwargs)
        self.initialized = False
        self.params = params
        self.values = values
        self.register_event_type('on_modified')

    def on_modified(self):
        pass

class OptionsView(BoxLayout):
    '''
    The main customization view which manages the various customization screens
    '''
    Builder.load_string('''
<OptionsView>:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: 0.9
        orientation: 'horizontal'
        ScrollContainer:
            size_hint_x: 0.3
            id: scroller
            do_scroll_x:False
            do_scroll_y:True
            GridLayout:
                padding: (sp(10), sp(10))
                spacing: sp(10)
                id: options
                row_default_height: root.height * 0.12
                row_force_default: True
                size_hint_y: None
                height: max(self.minimum_height, scroller.height)
                cols: 1
        ScreenManager:
            id: screens
            size_hint_x: 0.7
    BoxLayout:
        size_hint_y: 0.1
        orientation: 'horizontal'
        IconButton:
            id: confirm
            disabled: True
            text: u'\uf00c'
            on_release: root.confirm()
        IconButton:
            color: ColorScheme.get_primary()
            id: go_back
            text: u'\uf00d'
            on_release: root.cancel()    
    ''')

    def __init__(self, values, **kwargs):
        super(OptionsView, self).__init__(**kwargs)
        self.register_event_type('on_customized')
        self.register_event_type('on_close')
        screen_manager = self.ids.screens
        screen_manager.transition = SwapTransition()
        self.values = values

    def add_options_screen(self, screen, button):
        screen.bind(on_modified=self.on_modified)
        self.ids.screens.add_widget(screen)
        button.bind(on_press=lambda x: self.on_option(screen.name))
        self.ids.options.add_widget(button)

    def on_customized(self, values):
        pass

    def on_close(self):
        pass

    def confirm(self):
        self.dispatch('on_customized', self.values)
        self.dispatch('on_close')

    def cancel(self):
        self.dispatch('on_close')

    def on_modified(self, instance):
        self.ids.confirm.disabled = False

    def on_option(self, option):
        self.ids.screens.current = option
