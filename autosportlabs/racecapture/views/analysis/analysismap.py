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

from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from kivy.app import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics.transformation import Matrix
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import Screen, SwapTransition
from kivy.uix.popup import Popup
from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.racecapture.datastore import Filter
from autosportlabs.uix.color.colorgradient import SimpleColorGradient, HeatColorGradient
from iconbutton import IconButton, LabelIconButton


Builder.load_file('autosportlabs/racecapture/views/analysis/analysismap.kv')

class GradientBox(BoxLayout):
    '''
    Draws a color gradient box with the specified base color
    '''
    color = ObjectProperty([1.0, 1.0, 1.0], allownone = True)
    GRADIENT_STEP = 0.01
    
    def __init__(self, **kwargs):
        super(GradientBox, self).__init__(**kwargs)
        self.bind(pos=self._update_gradient, size=self._update_gradient)
        self._update_gradient()
        
    def on_color(self, instance, value):
        self._update_gradient()

    def _update_gradient(self, *args):
        '''
        Actually draws the gradient
        '''
        color_gradient = HeatColorGradient() if self.color is None else SimpleColorGradient(max_color=self.color)
        self.canvas.clear()
        step = GradientBox.GRADIENT_STEP
        pct = step
        with self.canvas:
            while pct < 1.0:
                color = color_gradient.get_color_value(pct)
                Color(*color)
                slice_width = self.width * step
                pos = (self.x + (self.width * pct), self.y)
                size = (slice_width, self.height)
                Rectangle(pos=pos, size=size)
                pct += step
        
class ColorLegend(BoxLayout):
    '''
    Represents a single color legend. The entire layout is drawn with the color specified.
    '''
    bar_color = ListProperty([1.0, 1.0, 1.0, 1.0])

class GradientLegend(BoxLayout):
    '''
    Represents a gradient legend, specified by min / max colors
    '''
    color = ObjectProperty([0.0, 0.0, 0.0, 1.0], allownone = True)

class GradientLapLegend(BoxLayout):
    '''
    A compound widget that presents a gradient color legend including session/lap and min/max values
    '''
    color = ObjectProperty([1.0, 1.0, 1.0], allownone = True)
    min_value = NumericProperty(0.0)
    max_value = NumericProperty(100.0)
    session = StringProperty('')
    lap = StringProperty('')
    
class LapLegend(BoxLayout):
    '''
    A compound widget that presents the the color legend with session/lap information
    '''
    color = ListProperty([1.0, 1.0, 1.0, 1.0])
    session = StringProperty('')
    lap = StringProperty('')

class AnalysisMap(AnalysisWidget):
    '''
    Displays a track map with options
    '''
    SCROLL_FACTOR = 0.15
    track_manager = ObjectProperty(None)
    datastore = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AnalysisMap, self).__init__(**kwargs)
        #Main settings
        self.track = None

        #State settings
        self.got_mouse = False
        self.heatmap_channel = None
        self.heatmap_channel_units = ''
        
        self.sources = {}
        Window.bind(on_motion=self.on_motion)
        
                
    def add_option_buttons(self):
        '''
        Add additional buttons needed by this widget
        '''
        self.append_option_button(IconButton(text=u'\uf0b2', on_press=self.on_center_map))
        
    def on_center_map(self, *args):
        '''
        Restore the track map to the default position/zoom/rotation
        '''
        scatter = self.ids.scatter
        scatter.scale = 1
        scatter.rotation = 0
        scatter.transform = Matrix().translate(self.pos[0], self.pos[1], 0)

    
    def on_options(self, *args):
        self.show_customize_dialog()
            
    def _set_heat_map(self, heatmap_channel):
        current_heatmap_channel = self.heatmap_channel

        for source in self.sources.itervalues():
            if current_heatmap_channel != heatmap_channel:
                self.remove_heat_values(source)
                if heatmap_channel:
                    self.add_heat_values(heatmap_channel, source)
                
        self.heatmap_channel = heatmap_channel
        self._refresh_lap_legends()
        self._update_legend_box_layout()
        
    def _update_legend_box_layout(self):
        '''
        This will set the size of the box that contains
        the lap legend widgets
        '''
        if self.heatmap_channel:
            self.ids.top_bar.size_hint_x=0.6
            self.ids.legend_box.size_hint_x=0.4
            units = self.heatmap_channel_units
            self.ids.heat_channel_name.text = '{} {}'.format(self.heatmap_channel, '' if len(units) == 0 else '({})'.format(units)) 
        else:
            self.ids.top_bar.size_hint_x=0.75
            self.ids.legend_box.size_hint_x=0.25
            self.ids.heat_channel_name.text = ''
        
    def _update_trackmap(self, values):
        track = self.track_manager.get_track_by_id(values.track_id)
        self._select_track(track)
    
    def _select_track(self, track):
        if track != None:
            self.ids.track.setTrackPoints(track.map_points)
            self.ids.track_name.text = '{} {}'.format(track.name, '' if track.configuration is None or track.configuration == '' else '({})'.format(track.configuration))
        else:
            self.ids.track_name.text = ''
            self.ids.track.setTrackPoints([])
        self.track = track
        
    def _customized(self, instance, values):
        self._update_trackmap(values)
        self._set_heat_map(values.heatmap_channel)
        
    def show_customize_dialog(self):
        '''
        Display the customization dialog for this widget
        '''
        current_track_id = None if self.track == None else self.track.track_id 
        content = CustomizeMapView(params=CustomizeParams(settings=self.settings, datastore=self.datastore, track_manager=self.track_manager),
                                   values=CustomizeValues(heatmap_channel=self.heatmap_channel, track_id=current_track_id)
                                   )
        popup = Popup(title="Customize Track Map", content=content, size_hint=(0.7, 0.7))
        content.bind(on_customized=self._customized)
        content.bind(on_close=lambda *args:popup.dismiss())  
        popup.open()
   
    def on_touch_down(self, touch):
        self.got_mouse = True
        return super(AnalysisMap, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        self.got_mouse = False
        return super(AnalysisMap, self).on_touch_up(touch)
        
    def on_motion(self, instance, event, motion_event):
        if self.got_mouse and motion_event.x > 0 and motion_event.y > 0 and self.collide_point(motion_event.x, motion_event.y):
            scatter = self.ids.scatter
            try:
                button = motion_event.button
                scale = scatter.scale
                if button == 'scrollup':
                    scale += self.SCROLL_FACTOR
                else:
                    if button == 'scrolldown':
                        scale -= self.SCROLL_FACTOR
                if scale < self.SCROLL_FACTOR:
                    scale = self.SCROLL_FACTOR
                scatter.scale = scale
            except:
                pass #no scrollwheel support
        
    def select_map(self, latitude, longitude):
        '''
        Find and display a nearby track by latitude / longitude
        :param latitude
        :type  latitude float
        :param longitude
        :type longitude float 
        '''
        if self.track_manager:
            point = GeoPoint.fromPoint(latitude, longitude)
            track = self.track_manager.find_nearby_track(point)
            self._select_track(track)

    def remove_reference_mark(self, source):
        self.ids.track.remove_marker(source)

    def add_reference_mark(self, source, color):
        '''
        Add a reference mark for the specified source
        :param source the key representing the reference mark
        :type source string
        :param color the color of the reference mark
        :type color list
        '''
        self.ids.track.add_marker(source, color)

    def update_reference_mark(self, source, point):
        self.ids.track.update_marker(str(source), point)

    def add_map_path(self, source_ref, path, color):
        '''
        Add a map path for the specified session/lap source reference
        :param source_ref the lap/session reference
        :type source_ref SourceRef
        :param path a list of points representing the map path
        :type path list
        :param color the path of the color
        :type color list
        '''
        source_key = str(source_ref)
        self.sources[source_key] = source_ref
        self.ids.track.add_path(source_key, path, color)
        if self.heatmap_channel:
            self.add_heat_values(self.heatmap_channel, source_ref)
            
        self._refresh_lap_legends()

    def remove_map_path(self, source_ref):
        '''
        Remove the map path for the specified session/lap source reference
        :param source_ref the source session/lap reference
        :type source_ref SourceRef
        '''
        source_key = str(source_ref)
        self.ids.track.remove_path(source_key)
        self.sources.pop(source_key, None)
        
        self._refresh_lap_legends()

    def _add_heat_value_results(self, channel, source_ref, query_data):
        '''
        Callback for adding channel data from the heat values
        :param channel the channel fetched
        :type channel string
        :param source_ref the session / lap reference
        :type source_ref SourceRef
        :param query_data the data results
        :type query_data ChannelData
        '''
        source_key = str(source_ref)
        values = query_data[channel].values
        channel_info = self.datastore.get_channel(channel)
        self.ids.track.set_heat_range(channel_info.min, channel_info.max)
        self.ids.track.add_heat_values(source_key, values)
        
    def add_heat_values(self, channel, source_ref):
        '''
        Add heat values to the track map
        :param channel the channel for the selected heat values
        :type channel string
        :param source_ref the source session/lap reference
        :type source_ref SourceRef
        '''
        def get_results(results):
            Clock.schedule_once(lambda dt: self._add_heat_value_results(channel, source_ref, results))
        self.datastore.get_channel_data(source_ref, [channel], get_results)

    def remove_heat_values(self, source_ref):
        '''
        Remove the heat values for the specified source reference
        :param source_ref the session/lap reference
        :type source_ref SourceRef
        '''
        source_key = str(source_ref)
        self.ids.track.remove_heat_values(source_key)
    
    def _refresh_lap_legends(self):
        '''
        Wholesale refresh the list of lap legends
        '''
        self.ids.legend_list.clear_widgets()

        multi_laps_selected = len(self.sources.keys()) > 1
        for source_ref in self.sources.itervalues():
            source_key = str(source_ref)
            #specify the heatmap color if multiple laps are selected, else use the default 
            #multi-color heatmap for a single lap selection
            path_color = self.ids.track.get_path(source_key).color if multi_laps_selected else None
            self._add_lap_legend(source_ref, path_color)

    def _add_lap_legend(self, source_ref, path_color):
        '''
        Update the lap legend for the specified source, 
        switching between normal and gradient as needed.
        :param source_ref the session/lap reference
        :type source_ref SourceRef
        :param path_color the color of the trackmap path
        :type path_color list
        '''
        heatmap_channel = self.heatmap_channel
        source_key = str(source_ref)
        if heatmap_channel:
            session_info = self.datastore.get_session_by_id(source_ref.session)
            channel_info = self.datastore.get_channel(heatmap_channel)
            self.heatmap_channel_units = channel_info.units
            lap_legend = GradientLapLegend(session = session_info.name, 
                                           lap = str(source_ref.lap),
                                           min_value = channel_info.min,
                                           max_value = channel_info.max,
                                           color = path_color
                                           )
        else:
            session_info = self.datastore.get_session_by_id(source_ref.session)
            path_color = self.ids.track.get_path(source_key).color
            lap_legend = LapLegend(color = path_color, 
                                   session = session_info.name, 
                                   lap = str(source_ref.lap))
        self.ids.legend_list.add_widget(lap_legend)
        
class CustomizeParams(object):
    '''
    A container class for holding multiple parameter for customization dialog
    '''
    def __init__(self, settings, datastore, track_manager, **kwargs):
        self.settings = settings
        self.datastore = datastore
        self.track_manager = track_manager

class CustomizeValues(object):
    '''
    A container class for holding customization values
    '''
    def __init__(self, heatmap_channel, track_id, **kwargs):
        self.heatmap_channel = heatmap_channel
        self.track_id = track_id
    
class BaseCustomizeMapView(Screen):
    '''
    A base class for a customization screen. This can be extended when adding the next option screen
    '''
    def __init__(self, params, values, **kwargs):
        super(BaseCustomizeMapView, self).__init__(**kwargs)
        self.initialized = False
        self.params = params
        self.values = values
        self.register_event_type('on_modified')
        
    def on_modified(self):
        pass
        
class HeatmapButton(LabelIconButton):
    pass

class TrackmapButton(LabelIconButton):
    pass

class CustomizeHeatmapView(BaseCustomizeMapView):
    '''
    The customization view for customizing the heatmap options
    '''
    available_channels = ListProperty()
    
    def __init__(self, params, values, **kwargs):
        super(CustomizeHeatmapView, self).__init__(params, values, **kwargs)
        self.ids.heatmap_channel.bind(on_channel_selected=self.channel_selected)
    
    def on_enter(self):
        if self.initialized == False:
            channels = self._get_available_channel_names()
            self.available_channels = channels
            self.ids.heatmap_channel.select_channel(self.values.heatmap_channel)
            
    def _get_available_channel_names(self):
        available_channels = self.params.datastore.channel_list
        return [str(c) for c in available_channels]
        
    def on_available_channels(self, instance, value):
        self.ids.heatmap_channel.channels = value
        
    def channel_selected(self, instance, value):
        value = None if len(value) == 0 else value[0]
        modified = self.values.heatmap_channel != value
        self.values.heatmap_channel = value
        if modified:
            self.dispatch('on_modified')
        
    def channel_cleared(self, *args):
        modified = self.values.heatmap_channel == None
        self.values.heatmap_channel = None
        if modified:
            self.dispatch('on_modified')
        
class CustomizeTrackView(BaseCustomizeMapView):
    '''
    The customization view for selecting a track to display
    '''
    track_id = StringProperty(None, allownone=True)
    def __init__(self, params, values, **kwargs):
        super(CustomizeTrackView, self).__init__(params, values, **kwargs)
        self.ids.track_browser.set_trackmanager(self.params.track_manager)
        self.ids.track_browser.bind(on_track_selected=self.track_selected)
        self.ids.track_browser.init_view()
        
    def track_selected(self, instance, value):
        if type(value) is set:
            self.values.track_id = None if len(value) == 0 else next(iter(value))
        self.dispatch('on_modified')

class CustomizeMapView(BoxLayout):
    '''
    The main customization view which manages the various customization screens
    '''
    def __init__(self, params, values, **kwargs):
        super(CustomizeMapView, self).__init__(**kwargs)
        self.values = values
        self.register_event_type('on_customized')
        self.register_event_type('on_close')
        
        screen_manager = self.ids.screens
        screen_manager.transition = SwapTransition()
        
        customize_heatmap_view = CustomizeHeatmapView(name='heat', params=params, values=values)
        customize_heatmap_view.bind(on_modified=self.on_modified)
                
        customize_track_view = CustomizeTrackView(name='track', params=params, values=values)
        customize_track_view.bind(on_modified=self.on_modified)
        
        self.customize_heatmap_view = customize_heatmap_view
        self.customize_track_view = customize_track_view
        
        screen_manager.add_widget(customize_heatmap_view)
        screen_manager.add_widget(customize_track_view)

        heatmap_option = HeatmapButton()
        heatmap_option.bind(on_press=lambda x: self.on_option('heat'))
        self.ids.options.add_widget(heatmap_option)
        
        trackmap_option = TrackmapButton()
        self.ids.options.add_widget(trackmap_option)
        trackmap_option.bind(on_press=lambda x: self.on_option('track'))
        
    def on_customized(self, values):
        pass
    
    def on_close(self):
        pass
    
    def confirm(self):
        self.dispatch('on_customized', self.values)
        self.dispatch('on_close')
    
    def cancel(self):
        self.dispatch('on_close')
        
    def on_modified(self, instance):
        self.ids.confirm.disabled = False
        
    def on_option(self, option):
        self.ids.screens.current = option
