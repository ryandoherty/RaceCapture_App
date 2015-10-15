import os
from threading import Thread
import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.screenmanager import Screen
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter
from autosportlabs.uix.button.featurebutton import FeatureButton
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from iconbutton import IconButton
from fieldlabel import FieldLabel

Builder.load_file('autosportlabs/racecapture/views/analysis/addstreamview.kv')

class AddStreamView(BoxLayout):
    def __init__(self, **kwargs):
        super(AddStreamView, self).__init__(**kwargs)
        settings = kwargs.get('settings')
        datastore = kwargs.get('datastore')
        stream_select_view = self.ids.streamSelectScreen
        stream_select_view.bind(on_connect_cloud=self.on_connect_cloud_stream)
        stream_select_view.bind(on_connect_wireless=self.on_connect_wireless_stream)
        stream_select_view.bind(on_connect_file=self.on_connect_file_stream)
                
        cloud_connect_view = self.ids.cloudConnectScreen
        cloud_connect_view.settings = settings
        cloud_connect_view.datastore = datastore
        
        wireless_connect_view = self.ids.wirelessConnectScreen
        wireless_connect_view.settings = settings
        wireless_connect_view.datastore = datastore
        
        file_connect_view = self.ids.fileConnectScreen
        file_connect_view.settings = settings
        file_connect_view.datastore = datastore
        file_connect_view.bind(on_connect_stream_complete=self.connect_stream_complete)
        
        self.register_event_type('on_stream_connected')
        
    def on_stream_connected(self, *args):
        pass
        
    def connect_stream_complete(self, *args):
        self.dispatch('on_stream_connected')
        
    def on_connect_file_stream(self, *args):
        self.ids.screens.current = 'file_connect'        

    def on_connect_cloud_stream(self, *args):
        self.ids.screens.current = 'cloud_connect'
        
    def on_connect_wireless_stream(self, *args):
        self.ids.screens.current = 'wireless_connect'
        
class AddStreamSelectView(Screen):    
    def __init__(self, **kwargs):
        super(AddStreamSelectView, self).__init__(**kwargs)
        self.register_event_type('on_connect_wireless')
        self.register_event_type('on_connect_cloud')
        self.register_event_type('on_connect_file')
            
    def connect_cloud_stream(self):
        self.dispatch('on_connect_cloud')
        
    def connect_wireless_stream(self):
        self.dispatch('on_connect_wireless')

    def connect_file_stream(self):
        self.dispatch('on_connect_file')

    def on_connect_cloud(self, *args):
        pass
    
    def on_connect_wireless(self, *args):
        pass
        
    def on_connect_file(self, *args):
        pass

class BaseStreamConnectView(Screen):
    settings = None
    datastore = None
    def __init__(self, **kwargs):
        super(BaseStreamConnectView, self).__init__(**kwargs)
        self.register_event_type('on_connect_stream_complete')
        
    def on_connect_stream_complete(self, *args):
        pass
    
class CloudConnectView(BaseStreamConnectView):
    pass

class WirelessConnectView(BaseStreamConnectView):
    pass

class FileConnectView(BaseStreamConnectView):
    def __init__(self, **kwargs):
        super(FileConnectView, self).__init__(**kwargs)

    def on_enter(self):
        log_import_view = self.ids.log_import
        log_import_view.bind(on_import_complete=self.import_complete)
        log_import_view.datastore = self.datastore
        log_import_view.settings = self.settings
                
    def import_complete(self, *args):
        self.dispatch('on_connect_stream_complete')

class LogImportWidget(BoxLayout):
    datastore = ObjectProperty(None)
    settings = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LogImportWidget, self).__init__(**kwargs)
        self.register_event_type('on_import_complete')
        self._log_path = None

    def on_import_complete(self, *args):
        pass
    
    def close_dstore_select(self, *args):
        self.datastore_select.dismiss()
        self.datastore_select = None

    def set_dstore_path(self, instance):
        filename = os.path.join(instance.path, instance.filename)        
        if not filename.endswith('.sq3'):
            filename = filename + '.sq3'
        self.ids.dstore_path.text = filename
        self.datastore_select.dismiss()

    def select_dstore(self):
        ok_cb = self.close_dstore_select
        content = SaveDialog(ok=self.set_dstore_path,
                             cancel=self.close_dstore_select,
                             filters=['*' + '.sq3'])
        self.datastore_select = Popup(title="Select Datastore", content=content, size_hint=(0.9, 0.9))
        self.datastore_select.open()

    def close_log_select(self, *args):
        self._log_select.dismiss()
        self._log_select = None

    def set_log_path(self, instance):
        path = instance.selection[0]
        self._log_path = path
        base_name = os.path.basename(path)
        session_name, file_extension = os.path.splitext(base_name)
        self.ids.log_path.text = base_name
        self.ids.session_name.text =  session_name
        
        self._log_select.dismiss()
        self.set_import_file_path(instance.path)

    def set_import_file_path(self, path):
        self.settings.userPrefs.set_pref('preferences', 'import_datalog_dir', path)
        
    def get_import_file_path(self):
        return self.settings.userPrefs.get_pref('preferences', 'import_datalog_dir')
 
    def select_log(self):
        ok_cb = self.close_log_select
        content = LoadDialog(ok=self.set_log_path,
                             cancel=self.close_log_select,
                             filters=['*' + '.log'],
                             user_path=self.get_import_file_path())
        self._log_select = Popup(title="Select Log", content=content, size_hint=(0.9, 0.9))
        self._log_select.open()

    def _loader_thread(self, logpath, session_name, session_notes):
        self.datastore.import_datalog(logpath, session_name, session_notes, self._update_progress)
        Clock.schedule_once(lambda dt: self.dispatch('on_import_complete'))

    def _update_progress(self, percent_complete=0):
        if self.ids.current_status.text != "Loading log records":
            self.ids.current_status.text = "Loading log records"
        self.ids.log_load_progress.value = int(percent_complete)

    def load_log(self):
        logpath = self._log_path
        session_name = self.ids.session_name.text.strip()
        session_notes = self.ids.session_notes.text.strip()
        
        dstore_path = self.settings.userPrefs.get_datastore_location()

        if not logpath:
            alertPopup("No Log Specified",
                      "Please select a log file to import")
            return

        if not os.path.isfile(logpath):
            alertPopup("Invalid log specified",
                      "Unable to find specified log file: {}. \nAre you sure it exists?".format(logpath))
            return

        if self.datastore.db_path != dstore_path:
            if self.datastore.is_open:
                self.datastore.close()
            
            if os.path.isfile(dstore_path):
                self.datastore.open_db(dstore_path)
            else:
                self.datastore.new(dstore_path)

        print "loading log", self.ids.log_path.text

        if session_name == '':
            alertPopup("No session name specified", "Please specify a name for this session")
            return

        self.ids.current_status.text = "Initializing Datastore"

        t = Thread(target=self._loader_thread, args=(logpath, session_name, session_notes))
        t.daemon = True
        t.start()

