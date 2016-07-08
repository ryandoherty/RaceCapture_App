import kivy
kivy.require('1.9.1')
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.app import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import sp
from kivy.metrics import dp
from iconbutton import IconButton

__all__ = ('alertPopup, confirmPopup, okPopup, editor_popup')

Builder.load_string('''
<ConfirmPopup>:
    cols:1
    Label:
        text: root.text
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        spacing: '5sp'
        IconButton:
            text: u'\uf00c'
            on_press: root.dispatch('on_answer', True)
        IconButton:
            text: u'\uf00d'
            color: ColorScheme.get_primary()            
            on_release: root.dispatch('on_answer', False)
            
<OkPopup>:
    cols:1
    Label:
        text: root.text
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        spacing: '5sp'
        IconButton:
            text: u'\uf00c'
            on_press: root.dispatch('on_answer', True)
            
            
<EditorPopup>:
    id: editor_popup
    cols:1
    BoxLayout:
        id: content
    GridLayout:
        id: buttons
        cols: 2
        size_hint_y: None
        height: '44sp'
        spacing: '5sp'
        IconButton:
            text: u'\uf00c'
            on_press: root.dispatch('on_answer', True)
        IconButton:
            text: u'\uf00d'
            color: ColorScheme.get_primary()            
            on_release: root.dispatch('on_answer', False)
            
''')
 
def alertPopup(title, msg):
    popup = Popup(title = title,
                      content=Label(text = msg),
                      size_hint=(None, None), size=(dp(600), dp(200)))
    popup.open()    
 
def confirmPopup(title, msg, answerCallback):
    content = ConfirmPopup(text=msg)
    content.bind(on_answer=answerCallback)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(None, None),
                    size=(dp(600),dp(200)),
                    auto_dismiss= False)
    popup.open()
    return popup
    
class ConfirmPopup(GridLayout):
    text = StringProperty()
    
    def __init__(self,**kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup,self).__init__(**kwargs)
        
    def on_answer(self, *args):
        pass    

def editor_popup(title, content, answerCallback):
    content = EditorPopup(content=content)
    content.bind(on_answer=answerCallback)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(0.7, 0.8),
                    auto_dismiss= False,
                  title_size=sp(18))
    popup.open()
    return popup
    
class EditorPopup(GridLayout):
    content = ObjectProperty(None)
    
    def __init__(self,**kwargs):
        self.register_event_type('on_answer')
        super(EditorPopup,self).__init__(**kwargs)
    
    def on_content(self, instance, value):
        Clock.schedule_once(lambda dt: self.ids.content.add_widget(value))
        
    def on_answer(self, *args):
        pass    

def okPopup(title, msg, answerCallback):
    content = OkPopup(text=msg)
    content.bind(on_ok=answerCallback)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(None, None),
                    size=(dp(600),dp(200)),
                    auto_dismiss= False)
    popup.open()
    return popup
    
class OkPopup(GridLayout):
    text = StringProperty()
    
    def __init__(self,**kwargs):
        self.register_event_type('on_ok')
        super(OkPopup,self).__init__(**kwargs)
        
    def on_ok(self, *args):
        pass    