import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.treeview import TreeView, TreeViewLabel
from utils import *
from autosportlabs.racecapture.views.status.components.gps import *
from autosportlabs.racecapture.views.status.components.bluetooth import *
from autosportlabs.racecapture.views.status.components.cellular import *
from autosportlabs.racecapture.views.status.components.logging import *
from autosportlabs.racecapture.views.status.components.system import *
from autosportlabs.racecapture.views.status.components.telemetry import *
from autosportlabs.racecapture.views.status.components.track import *

Builder.load_file('autosportlabs/racecapture/views/status/statusview.kv')

# Simple extension of Kivy's TreeViewLabel so we can add on our own properties
# to it for easier view tracking
class LinkedTreeViewLabel(TreeViewLabel):
    view = None


# Shows RCP's entire status, getting the values by firing an 'on_status_requested' event
# that is heard by other code that talks to RCP. Data is then returned back to this
# class asynchronously.
class StatusView(Screen):

    #JSON object that contains the status of RCP
    status = None

    menu_items = {
        'GPS': {'view': GPSStatusView, 'instance': None},
        'Telemetry': {'view': TelemetryStatusView, 'instance': None},
        'Track': {'view': TrackStatusView, 'instance': None},
        'Logging': {'view': LoggingStatusView, 'instance': None},
        'Bluetooth': {'view': BluetoothStatusView, 'instance': None},
        'Cellular': {'view': CellularStatusView, 'instance': None},
        'System': {'view': SystemStatusView, 'instance': None},
    }

    menu_select_color = [1.0,0,0,0.6]

    def __init__(self, **kwargs):
        super(StatusView, self).__init__(**kwargs)
        self._content_container = self.ids.content
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_status_requested')

        self.status ={
            "system":{
                "model":'RCP',
                "ver_major":2,
                "ver_minor":8,
                "ver_bugfix":0,
                "serial":'45FGEJ',
                "uptime":1429478284000
            },
            "GPS":{
                "init":1,
                "qual": 1,
                "lat": 39.536569,
                "lon": -122.336868,
                "sats": 4,
                "dop": 1.2
            },
            "cell":{
                "init": 3,
                "IMEI": '23r5jkdsfj34f',
                "sig_str": 3,
                "number":'4085631823'
            },
            "bt":{
                "init": 2,
            },
            "logging":{
                "status": 2,
                "started": 1429478284000
            },
            "track":{
                "status": 2,
                "trackId": 1429478284000,
                "inLap": 0,
                "armed": 1
            },
            "telemetry" :{
                "status": 2,
                "started": 1429478284000
            }
        }

        self._build_menu()
        self.dispatch('on_status_requested')

    def _build_menu(self):
        menu_node = self.ids.menu

        for item, config in self.menu_items.iteritems():
            label = LinkedTreeViewLabel(text=item)
            label.color_selected = self.menu_select_color
            menu_node.add_node(label)

        menu_node.bind(selected_node=self._on_menu_select)

    def _on_menu_select(self, instance, value):
        self._content_container.clear_widgets()
        view_info = self.menu_items[value.text]

        if not view_info['instance']:
            view_info['instance'] = view_info['view'](self.status)

        self._content_container.add_widget(view_info['instance'])

    def update(self):
        #loop through views, update with new status
        for item, config in self.menu_items.iteritems():
            if config['instance']:
                config['instance'].update_status(self.status)

    def on_status_updated(self, status):
        self.status = status
        self.update()
        pass

    def on_tracks_updated(self, track_manager):
        pass

    def on_status_requested(self):
        pass

