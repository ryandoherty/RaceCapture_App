import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.properties import ListProperty
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import sp
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.adapters.listadapter import ListAdapter
from kivy.logger import Logger
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.theme.color import ColorScheme

Builder.load_file('autosportlabs/racecapture/views/analysis/sessionbrowser.kv')

class LapItemButton(ToggleButton):
    background_color_normal = ColorScheme.get_dark_background()
    background_color_down = ColorScheme.get_primary()

    def __init__(self, session, lap, laptime, **kwargs):
        super(LapItemButton, self).__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = self.background_color_normal
        self.session = session
        self.lap = lap
        self.laptime = laptime

    def on_state(self, instance, value):
        self.background_color = self.background_color_down if value == 'down' else self.background_color_normal

class Session(BoxLayout):
    data_items = ListProperty()
    def __init__(self, ses_id, name, notes, **kwargs):
        super(Session, self).__init__(**kwargs)
        self.ses_id = ses_id
        self.name = name
        self.notes = notes
        self.lap_count = 0

    def on_select(self, value):
        pass

    def append_lap(self, session, lap, laptime):
        text = str(int(lap)) + ' :: ' + str(laptime)
        lapitem = LapItemButton(session=session, text=text, lap=lap, laptime=laptime)
        self.ids.lap_list.add_widget(lapitem)
        self.lap_count += 1
        return lapitem

class SessionAccordionItem(AccordionItem):
    def __init__(self, **kwargs):
        self.session_widget = None
        super(SessionAccordionItem, self).__init__(**kwargs)
        self.register_event_type('on_collapsed')
    
    def on_collapsed(self, value):
        pass
            
    def on_collapse(self, instance, value):
        super(SessionAccordionItem, self).on_collapse(instance, value)
        self.dispatch('on_collapsed', value) 
    
class SessionBrowser(BoxLayout):
    ITEM_HEIGHT = sp(50)
    SESSION_TITLE_HEIGHT = sp(20)
    
    def __init__(self, **kwargs):
        super(SessionBrowser, self).__init__(**kwargs)
        self.register_event_type('on_lap_selected')
        accordion = Accordion(orientation='vertical', size_hint=(1.0, None))
        sv = ScrollContainer(size_hint=(1.0, 1.0), do_scroll_x=False)
        sv.add_widget(accordion)
        self._accordion = accordion
        self.add_widget(sv)
            
    def on_session_collapsed(self, instance, value):
        if value == False:
            session_count = len(self._accordion.children)
            self._accordion.height = (self.ITEM_HEIGHT * instance.session_widget.lap_count) + (session_count * self.SESSION_TITLE_HEIGHT)
        
    def append_session(self, ses_id, name, notes):
        session = Session(ses_id=ses_id, name=name, notes=notes)
        item = SessionAccordionItem(title=name)
        item.session_widget = session
        item.bind(on_collapsed=self.on_session_collapsed)
        item.add_widget(session)
        self._accordion.add_widget(item)
        return session
        
    def append_lap(self, session, lap, laptime):
        lapitem = session.append_lap(session.ses_id, lap, laptime)
        lapitem.bind(on_press=self.lap_selected)

    def on_lap_selected(self, *args):
        pass
    
    def lap_selected(self, instance):
        selected = instance.state == 'down'
        self.dispatch('on_lap_selected', SourceRef(instance.lap, instance.session), selected)
        
    def clear_sessions(self):
        self._accordion.clear_widgets()

