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
import kivy
kivy.require('1.9.0')
from kivy.logger import Logger
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.animation import Animation
from kivy.properties import ObjectProperty
from kivy.uix.behaviors import ButtonBehavior

FLYIN_PANEL_LAYOUT='''
<FlyinPanel>:
    size_hint: (1,1)
    BoxLayout:
        id: flyin
        orientation: 'vertical'
        size_hint: (1,1)
        pos: (root.width - self.width, self.height)
        size_hint_x: 0.25
        canvas.before:
            Color:
                rgba: (0,0,0,1)
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            id: content
            size_hint: (1,0.95)
        FlyinHandle:
            canvas.before:
                Color:
                    rgba: (1,0,0,1)
                Rectangle:
                    pos: self.pos
                    size: self.size
            id: handle
            size_hint: (1,0.05)
            on_press: root.toggle()
'''

class FlyinPanelException(Exception):
    '''Raised when add_widget is called incorrectly on FlyinPanel
    '''

class FlyinHandle(ButtonBehavior, AnchorLayout):
    pass
    
class FlyinPanel(FloatLayout):
    
    content = ObjectProperty()
    handle = ObjectProperty()
    
    #how long we wait to auto-dismiss session list
    #after a perioud of disuse
    SESSION_HIDE_DELAY = 3.0
    TRANSITION_STYLE = 'in_out_elastic'
    SHOW_POSITION = 0
#    contents = ObjectProperty(None, allownone=True)
#    handle = ObjectProperty(None, allownone=True)
    
    def __init__(self, **kwargs):
        Builder.load_string(FLYIN_PANEL_LAYOUT)
        super(FlyinPanel, self).__init__(**kwargs)
        self.hide_decay = Clock.create_trigger(lambda dt: self.hide(), self.SESSION_HIDE_DELAY)
        Clock.schedule_once(lambda dt: self.show())
        self.hide_decay()     
        
    def add_widget(self, widget):
        if len(self.children) == 0:
            super(FlyinPanel, self).add_widget(widget)
        else:
            if len(self.ids.content.children) == 0:
                self.ids.content.add_widget(widget)
            elif len(self.ids.handle.children) == 0:
                self.ids.handle.add_widget(widget)
            else:
                raise FlyinPanelException('Can only add one content widget and one handle widget to FlyinPanel')
           
    def schedule_hide(self):
        self.hide_decay()
    
    def cancel_hide(self):
        Clock.unschedule(self.hide_decay)

    def hide(self):
        b_height = self.ids.handle.height
        anim = Animation(y=(self.height - b_height), t=self.TRANSITION_STYLE)
        anim.start(self.ids.flyin)
        
    def show(self):
        anim = Animation(y=self.SHOW_POSITION, t=self.TRANSITION_STYLE)
        anim.start(self.ids.flyin)
    
    @property
    def is_hidden(self):
        return self.ids.flyin.y != self.SHOW_POSITION
    
    def toggle(self):
        self.show() if self.is_hidden else self.hide()
    