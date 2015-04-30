import kivy
kivy.require('1.8.0')
from kivy.clock import Clock
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from datetime import timedelta
from utils import *
from fieldlabel import FieldLabel

Builder.load_file('autosportlabs/racecapture/views/status/statusview.kv')

RAW_STATUS_BGCOLOR_1 = [0  , 0  , 0  , 1.0]
RAW_STATUS_BGCOLOR_2 = [0.10, 0.10, 0.10, 1.0]

class StatusLabel(FieldLabel):
    backgroundColor = ObjectProperty(RAW_STATUS_BGCOLOR_1)

class StatusTitle(StatusLabel):
    pass

class StatusValue(StatusLabel):
    pass

# Simple extension of Kivy's TreeViewLabel so we can add on our own properties
# to it for easier view tracking
class LinkedTreeViewLabel(TreeViewLabel):
    id = None

# Shows RCP's entire status, getting the values by polling RCP for its status
class StatusView(Screen):

    _bg_current = RAW_STATUS_BGCOLOR_1
    
    STATUS_QUERY_INTERVAL = 2.0

    #Dict object that contains the status of RCP
    status = ObjectProperty(None)

    #Currently selected menu item
    _selected_item = None

    _menu_built = False

    #Track manager for getting track name
    track_manager = None

    #Comms object for communicating with RCP
    rc_api = None

    #Used for building the left side menu
    _menu_keys = {
        "system": "System Status",
        "GPS": "GPS",
        "cell": "Cellular",
        "bt": "Bluetooth",
        "logging": "Logging",
        "track": "Track",
        "telemetry": "Telemetry"
    }

    #Dict for getting English text for status enums
    _enum_keys = {
        'GPS': {
            'init': [
                'Not initialized',
                'Initialized',
                'Error initializing'
            ],
            'qual': [
                'No fix',
                'Weak',
                'Acceptable',
                'Strong'
            ]
        },
        'cell': {
            'init': [
                'Not initialized',
                'Initialized',
                'Error initializing'
            ]
        },
        'bt': {
            'init': [
                'Not initialized',
                'Initialized',
                'Error initializing'
            ]
        },
        'logging': {
            'status': [
                'Not logging',
                'Logging',
                'Error logging'
            ]
        },
        'track': {
            'status': [
                'Searching',
                'Fixed start/finish',
                'Detected'
            ]
        },
        'telemetry': {
            'status': [
                'Idle',
                'Connected',
                'Connection terminated',
                'Device ID rejected',
                'Data connection failed. SIM card is valid, either no data plan is associated or the plan has expired.',
                'Failed to connect to server',
                'Data connection failed. APN settings possibly wrong.',
                'Unable to join cellular network. Bad or missing SIM card.'
            ]
        }
    }

    _menu_node = None
    menu_select_color = [1.0,0,0,0.6]

    def __init__(self, track_manager, rc_api, **kwargs):
        super(StatusView, self).__init__(**kwargs)
        self.track_manager = track_manager
        self.rc_api = rc_api
        self.register_event_type('on_tracks_updated')
        self.rc_api.addListener('status', self._on_status_updated)
        self._menu_node = self.ids.menu
        self._menu_node.bind(selected_node=self._on_menu_select)

    def start_status(self):
        Clock.schedule_interval(lambda dt: self.rc_api.get_status(), self.STATUS_QUERY_INTERVAL)
        
    def _build_menu(self):
        if self._menu_built:
            return

        default_node = None

        for item, config in self.status.iteritems():
            text = self._menu_keys[item] if item in self._menu_keys else item

            label = LinkedTreeViewLabel(text=text)

            label.id = item
            label.color_selected = self.menu_select_color
            node = self._menu_node.add_node(label)

            if item == 'system':
                default_node = node

        self._menu_built = True

        if default_node:
            self._menu_node.select_node(default_node)

    def _on_menu_select(self, instance, value):
        self._selected_item = value.id
        self.update()

    def _on_status_updated(self, status):
        self.status = status['status']
        
    def update(self):
        _bg_current = RAW_STATUS_BGCOLOR_1
        
        if self._selected_item in self._menu_keys:
            text = self._menu_keys[self._selected_item]
        else:
            text = self._selected_item

        self.ids.name.text = text
        self.ids.status_grid.clear_widgets()

        function_name = ('render_' + self._selected_item).lower()

        #Generic way of not having to create a long switch or if/else block
        #to call each render function
        if function_name in dir(self):
            getattr(self, function_name)()
        else:
            self.render_generic(self._selected_item)

    def render_generic(self, section):
        status = self.status[section]

        for item, value in status.iteritems():
            self._add_item(item, value)

    def render_system(self):
        version = '.'.join(
            [
                str(self.status['system']['ver_major']),
                str(self.status['system']['ver_minor']),
                str(self.status['system']['ver_bugfix'])
            ]
        )

        self._add_item('Version', version)
        self._add_item('Serial Number', self.status['system']['serial'])

        uptime = timedelta(seconds=(self.status['system']['uptime']/1000))
        self._add_item('Uptime', uptime)

    def render_gps(self):
        status = self.status['GPS']

        init_status = self._get_enum_definition('GPS', 'init', status['init'])
        quality = self._get_enum_definition('GPS', 'qual', status['qual'])
        location = str(status['lat']) + ', ' + str(status['lon'])
        satellites = status['sats']
        dop = status['DOP']

        self._add_item('Status', init_status)
        self._add_item('GPS Quality', quality)
        self._add_item('Location', location)
        self._add_item('Satellites', satellites)
        self._add_item('Dilution of precision', dop)

    def render_cell(self):
        status = self.status['cell']

        init_status = self._get_enum_definition('cell', 'init', status['init'])
        imei = status['IMEI']
        signal_strength = status['sig_str']
        number = status['number']

        self._add_item('Status', init_status)
        self._add_item('IMEI', imei)
        self._add_item('Signal strength', signal_strength)
        self._add_item('Phone Number', number)

    def render_bt(self):
        status = self.status['bt']

        init_status = self._get_enum_definition('bt', 'init', status['init'])
        self._add_item('Status', init_status)

    def render_logging(self):
        status = self.status['logging']

        init_status = self._get_enum_definition('logging', 'status', status['status'])
        duration = timedelta(seconds=(status['dur']/1000))

        self._add_item('Status', init_status)
        self._add_item('Logging for', duration)

    def render_telemetry(self):
        status = self.status['telemetry']

        init_status = self._get_enum_definition('telemetry', 'status', status['status'])
        duration = timedelta(seconds=(status['dur']/1000))

        self._add_item('Status', init_status)
        self._add_item('Logging for', duration)

    def render_track(self):
        status = self.status['track']

        init_status = self._get_enum_definition('track', 'status', status['status'])

        if status['status'] == 1:
            track_name = 'User defined'
        else:
            if status['trackId'] != 0:
                track = self.track_manager.findTrackByShortId(status['trackId'])

                if track is None:
                    track_name = 'Track not found'
                else:
                    track_name = track.name
            else:
                track_name = 'No track detected'

        in_lap = 'Yes' if status['inLap'] == 1 else 'No'
        armed = 'Yes' if status['armed'] == 1 else 'No'

        self._add_item('Status', init_status)
        self._add_item('Track', track_name)
        self._add_item('In lap', in_lap)
        self._add_item('Armed', armed)

    def _add_item(self, label, data):
        label_widget = StatusTitle(text=label)
        data_widget = StatusValue(text=str(data))
        self.ids.status_grid.add_widget(label_widget)
        self.ids.status_grid.add_widget(data_widget)
        if len(self.ids.status_grid.children) / 2 % 2 == 0:
            bg_color = RAW_STATUS_BGCOLOR_2
        else:
            bg_color = RAW_STATUS_BGCOLOR_1
            
        label_widget.backgroundColor = bg_color
        data_widget.backgroundColor = bg_color        

    
    def on_status(self, instance, value):
        self._build_menu()
        self.update()

    # Generalized function for getting an enum's English
    # equivalent. If the value is not found, the enum is returned
    def _get_enum_definition(self, section, subsection, value):
        val = value

        if section in self._enum_keys and subsection in self._enum_keys[section]:
            if len(self._enum_keys[section][subsection]) > value:
                val = self._enum_keys[section][subsection][value]

        return val

    def on_tracks_updated(self, track_manager):
        pass

