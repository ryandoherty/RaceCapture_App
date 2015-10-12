import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.properties import ListProperty
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import sp
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.adapters.listadapter import ListAdapter
from kivy.logger import Logger

Builder.load_file('autosportlabs/racecapture/views/analysis/sessionbrowser.kv')

class LapNode(BoxLayout):
    lap = 0
    session = 0
    def __init__(self, **kwargs):
        super(LapNode, self).__init__(**kwargs)
        self.register_event_type('on_lap_selected')
        lap = int(kwargs.get('lap'))
        session = int(kwargs.get('session'))
        laptime = kwargs.get('laptime')
        self.ids.lap.text = str(lap)
        self.ids.laptime.text = format_laptime(laptime)
        self.lap = lap
        self.session = session
        
    def on_lap_selected(self, *args):
        pass
    
    def lap_selected(self, instance, value):
        self.dispatch('on_lap_selected', SourceRef(self.lap, self.session), value)
        
class SessionNode(BoxLayout):
    def __init__(self, **kwargs):
        super(SessionNode, self).__init__(**kwargs)
        name = kwargs.get('name', '(unnamed)')
        notes = kwargs.get('notes', '')
        self.ids.name.text = self.notes = str(name)
        self.notes = str(notes)

class LapItemButton(ToggleButton):
    background_color_normal = ListProperty([1, 1, 1, 0])
    background_color_down = ListProperty([1, 1, 1, 0.5])

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

    def on_select(self, value):
        pass

    def append_lap(self, session, lap, laptime):
        text = str(lap) + ' ' + str(laptime)
        lapitem = LapItemButton(session=session, text=text, lap=lap, laptime=laptime)
        self.ids.lap_list.add_widget(lapitem)
        return lapitem

class SessionBrowser(BoxLayout):
    def __init__(self, **kwargs):
        super(SessionBrowser, self).__init__(**kwargs)
        self.register_event_type('on_lap_selected')
        accordion = Accordion(orientation='vertical', size_hint=(1.0, None))
        accordion.height = 400
        sv = ScrollContainer(size_hint=(1.0, 1.0), do_scroll_x=False)
        sv.add_widget(accordion)
        self._accordion = accordion
        self.add_widget(sv)
    
    def append_session(self, ses_id, name, notes):
        session = Session(ses_id=ses_id, name=name, notes=notes)
        item = AccordionItem(title=name)
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
        pass

