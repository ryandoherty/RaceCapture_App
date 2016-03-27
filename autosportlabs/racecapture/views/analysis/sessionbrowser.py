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
#have received a copy of the GNU General Public License along with
#this code. If not, see <http://www.gnu.org/licenses/>.

import kivy
kivy.require('1.9.0')
from kivy.app import Builder
from kivy.properties import ListProperty
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import sp
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.anchorlayout import AnchorLayout
from kivy.adapters.listadapter import ListAdapter
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from autosportlabs.racecapture.datastore import DatastoreException, Filter
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from autosportlabs.racecapture.views.analysis.markerevent import SourceRef
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.theme.color import ColorScheme
from autosportlabs.racecapture.views.analysis.sessioneditorview import SessionEditorView
from autosportlabs.racecapture.views.util.alertview import confirmPopup, alertPopup, editor_popup
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from fieldlabel import FieldLabel
import traceback

Builder.load_file('autosportlabs/racecapture/views/analysis/sessionbrowser.kv')

class NoSessionsAlert(FieldLabel):
    pass
    
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
    def __init__(self, session_id, name, notes, **kwargs):
        super(Session, self).__init__(**kwargs)
        self.session_id = session_id
        self.name = name
        self.notes = notes
        self.register_event_type('on_delete_session')
        self.register_event_type('on_edit_session')
    
    @property
    def item_count(self):
        return len(self.ids.lap_list.children)

    def append_lap(self, session, lap, laptime):
        text = '{} :: {}'.format(int(lap), format_laptime(laptime))
        lapitem = LapItemButton(session=session, text=text, lap=lap, laptime=laptime)
        self.ids.lap_list.add_widget(lapitem)
        return lapitem
    
    def append_label(self, message):
        self.ids.lap_list.add_widget(FieldLabel(text=message, halign='center'))
        
    def on_delete_session(self, value):
        pass

    def on_edit_session(self, value):
        pass
        
    def edit_session(self):
        self.dispatch('on_edit_session', self.session_id)
        
    def prompt_delete_session(self):
        def _on_answer(instance, answer):
            if answer:
                self.dispatch('on_delete_session', self.session_id)
            popup.dismiss()
            
        popup = confirmPopup('Confirm', 'Delete Session {}?'.format(self.name), _on_answer)


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
    
class SessionBrowser(AnchorLayout):
    ITEM_HEIGHT = sp(40)
    SESSION_TITLE_HEIGHT = sp(45)
    datastore = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super(SessionBrowser, self).__init__(**kwargs)
        self.register_event_type('on_lap_selected')
        accordion = Accordion(orientation='vertical', size_hint=(1.0, None))
        sv = ScrollContainer(size_hint=(1.0, 1.0), do_scroll_x=False)
        self.selected_laps = {}
        self.current_laps = {}
        sv.add_widget(accordion)
        self._accordion = accordion
        self.add_widget(sv)
    
    def on_datastore(self, instance, value):
        Clock.schedule_once(lambda dt: self.refresh_session_list())
        
    def refresh_session_list(self):
        try:
            self.clear_sessions()
            sessions = self.datastore.get_sessions()
            f = Filter().gt('LapCount', 0)
            session = None
            for session in sessions:
                session = self.append_session(session_id=session.session_id, name=session.name, notes=session.notes)
                dataset = self.datastore.query(sessions=[session.session_id],
                                        channels=['LapCount', 'LapTime'],
                                        data_filter=f,
                                        distinct_records=True)
        
                records = dataset.fetch_records()
                lap_count = 0
                for r in records:
                    lap_id = int(r[1])
                    laptime = r[2]
                    self.append_lap(session, lap_id, laptime)
                    lap_count += 1
                if lap_count == 0:
                    session.append_label('No Laps')

            self.sessions = sessions
            self.ids.session_alert.text = '' if session else 'No Sessions'
                
        except Exception as e:
            Logger.error('AnalysisView: unable to fetch laps: {}\n\{}'.format(e, traceback.format_exc()))            
        
    def on_session_collapsed(self, instance, value):
        if value == False:
            session_count = len(self._accordion.children)
            #minimum space needed in case there are no laps in the session, plus the session toolbar
            item_count = max(instance.session_widget.item_count, 1) + 1
            session_items_height = (item_count * self.ITEM_HEIGHT)
            session_titles_height = (session_count * self.SESSION_TITLE_HEIGHT)
            accordion_height = session_items_height + session_titles_height
            self._accordion.height = accordion_height
        
    def append_session(self, session_id, name, notes):
        session = Session(session_id=session_id, name=name, notes=notes)
        item = SessionAccordionItem(title=name)
        item.session_widget = session
        item.bind(on_collapsed=self.on_session_collapsed)
        session.bind(on_delete_session=self.delete_session)
        session.bind(on_edit_session=self.edit_session)
        item.add_widget(session)
        self._accordion.add_widget(item)
        return session
        
    def edit_session(self, instance, session_id):
        def _on_answer(instance, answer):
            if answer:
                session_name = session_editor.session_name
                if not session_name or len(session_name) == 0:
                    alertPopup('Error', 'A session name must be specified')
                    return
                session.name = session_editor.session_name
                session.notes = session_editor.session_notes
                self.datastore.update_session(session)
                self.refresh_session_list()
            popup.dismiss()
        
        session = self.datastore.get_session_by_id(session_id, self.sessions)
        session_editor = SessionEditorView()
        session_editor.session_name = session.name
        session_editor.session_notes = session.notes
        popup = editor_popup('Edit Session', session_editor, _on_answer)
    
    def delete_session(self, instance, id):
        try:
            self.datastore.delete_session(id)
            Logger.info('SessionBrowser: Session {} deleted'.format(id))
            self.refresh_session_list()
        except DatastoreException as e:
            alertPopup('Error', 'There was an error deleting the session:\n{}'.format(e))
            Logger.error('SessionBrowser: Error deleting session: {}\n\{}'.format(e, traceback.format_exc()))
        
    def append_lap(self, session, lap, laptime):
        lapitem = session.append_lap(session.session_id, lap, laptime)
        source_key = str(SourceRef(lap, session.session_id))
        if self.selected_laps.get(source_key):
            lapitem.state = 'down'
        lapitem.bind(on_press=self.lap_selected)
        self.current_laps[source_key] = lapitem

    def on_lap_selected(self, *args):
        pass
    
    def lap_selected(self, instance):
        self._select_lap(instance)
    
    def _select_lap(self, instance):
        selected = instance.state == 'down'
        source_ref = SourceRef(instance.lap, instance.session)
        self.dispatch('on_lap_selected', source_ref, selected)
        source_key = str(source_ref)
        if selected:
            self.selected_laps[source_key] = instance
        else:
            self.selected_laps.pop(source_key, None)
            
    def clear_sessions(self):
        self.current_laps = {}
        self._accordion.clear_widgets()
        
    def select_lap(self, session_id, lap_id, selected):
        source_ref = SourceRef(lap_id, session_id)
        source_key = str(source_ref)
        lap_instance = self.current_laps.get(source_key)
        if lap_instance: 
            lap_instance.state = 'down' if selected else 'normal'
            self._select_lap(lap_instance)
        
