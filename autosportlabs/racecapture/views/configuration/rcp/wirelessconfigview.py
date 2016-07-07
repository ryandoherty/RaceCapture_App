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
kivy.require('1.9.1')
from kivy.app import Builder

from kivy.core.window import Window
from kivy.properties import ObjectProperty
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from kivy.logger import Logger
from autosportlabs.racecapture.views.configuration.rcp.wireless.bluetoothconfigview import BluetoothConfigView
from autosportlabs.racecapture.views.configuration.rcp.wireless.cellularconfigview import CellularConfigView
from autosportlabs.racecapture.views.configuration.rcp.wireless.wificonfigview import WifiConfigView

WIRELESS_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/wirelessconfigview.kv'


class WirelessConfigView(BaseConfigView):
    Builder.load_file(WIRELESS_CONFIG_VIEW_KV)

    def __init__(self, base_dir, config, capabilities, **kwargs):
        super(WirelessConfigView, self).__init__(**kwargs)

        self.register_event_type('on_config_updated')
        self.register_event_type('on_config_modified')
        self.base_dir = base_dir
        self.rcp_capabilities = capabilities
        self.rcp_config = config
        self._views = []

        self._render()
        self._attach_event_handlers()

    def _render(self):
        if not self.rcp_capabilities or (self.rcp_capabilities and self.rcp_capabilities.has_bluetooth):
            bluetooth_view = BluetoothConfigView(self.rcp_config)
            self.ids.wireless_settings.add_widget(bluetooth_view, index=0)
            self._views.append(bluetooth_view)

        if not self.rcp_capabilities or (self.rcp_capabilities and self.rcp_capabilities.has_wifi):
            wifi_view = WifiConfigView(self.base_dir, self.rcp_config)
            self.ids.wireless_settings.add_widget(wifi_view, index=0)
            self._views.append(wifi_view)

        if not self.rcp_capabilities or (self.rcp_capabilities and self.rcp_capabilities.has_cellular):
            cellular_view = CellularConfigView(self.base_dir, self.rcp_config)
            self.ids.wireless_settings.add_widget(cellular_view, index=0)
            self._views.append(cellular_view)



    def _attach_event_handlers(self):
        for view in self._views:
            view.bind(on_modified=self._on_views_modified)

    def on_config_updated(self, config):
        # Just destroy everything, re-render
        self.rcp_config = config
        self._update_view_configs()

    def _update_view_configs(self):
        for view in self._views:
            view.config_updated(self.rcp_config)

    def _on_views_modified(self, *args):
        Logger.debug("WirelessConfigView: _on_views_modified args: {}".format(args))
        Logger.debug("Got view modified")
        self.dispatch('on_config_modified')

    def on_config_modified(self, *args):
        pass
