import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.label import Label
from utils import *

Builder.load_file('autosportlabs/racecapture/views/status/statusview.kv')

# Simple extension of Kivy's TreeViewLabel so we can add on our own properties
# to it for easier view tracking
class LinkedTreeViewLabel(TreeViewLabel):
    id = None

# Shows RCP's entire status, getting the values by firing an 'on_status_requested' event
# that is heard by other code that talks to RCP. Data is then returned back to this
# class asynchronously.
class StatusView(Screen):

    #JSON object that contains the status of RCP
    status = None
    selected_item = None

    menu_keys = {
        "system": "System Status",
        "GPS": "GPS",
        "cell": "Cellular",
        "bt": "Bluetooth",
        "logging": "Logging",
        "track": "Track",
        "telemetry": "Telemetry"
    }

    enum_keys = {
        'system': {

        },
        'GPS': {

        },
        'cell': {

        },
        'bt': {

        },
        'logging': {

        },
        'track': {

        },
        'telemetry': {

        }
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
            },
            "unknown": {
                'foo':'bar'
            }
        }

        self._build_menu()
        self.dispatch('on_status_requested')

    def _build_menu(self):
        menu_node = self.ids.menu

        for item, config in self.status.iteritems():
            text = self.menu_keys[item] if item in self.menu_keys else item

            label = LinkedTreeViewLabel(text=text)

            label.id = item
            label.color_selected = self.menu_select_color
            menu_node.add_node(label)

        menu_node.bind(selected_node=self._on_menu_select)

    def _on_menu_select(self, instance, value):
        self.selected_item = value.id
        self.update()

    def update(self):
        if self.selected_item in self.menu_keys:
            text = self.menu_keys[self.selected_item]
        else:
            text = self.selected_item

        self.ids.name.text = text

        function_name = 'render_' + self.selected_item

        #Generic way of not having to create a long switch or if/else block
        #to call each render function
        if function_name in dir(self):
            getattr(self, function_name)()

    def render_system(self):
        version = '.'.join(
            [
                str(self.status['system']['ver_major']),
                str(self.status['system']['ver_minor']),
                str(self.status['system']['ver_bugfix'])
            ]
            )


        version_label = Label(text='Version')
        version_number = Label(text=version)
        self.ids.grid.add_widget(version_label)
        self.ids.grid.add_widget(version_number)

    def on_status_updated(self, status):
        self.status = status
        self.update()
        pass

    def on_status_requested(self):
        pass

    def on_tracks_updated(self, track_manager):
        pass

    def on_status_requested(self):
        pass

