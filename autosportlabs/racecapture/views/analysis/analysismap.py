from kivy.properties import ObjectProperty, ListProperty, StringProperty
from kivy.app import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics.transformation import Matrix
from kivy.uix.screenmanager import Screen, SwapTransition
from kivy.uix.popup import Popup
from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.racecapture.datastore import Filter
from iconbutton import IconButton, LabelIconButton

Builder.load_file('autosportlabs/racecapture/views/analysis/analysismap.kv')

class AnalysisMap(AnalysisWidget):
    SCROLL_FACTOR = 0.15
    track_manager = ObjectProperty(None)
    datastore = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AnalysisMap, self).__init__(**kwargs)
        #Main settings
        self.current_heat_channel = None
        self.track = None

        #State settings
        self.got_mouse = False
        self.heat_enabed = False
        self.sources = {}
        Window.bind(on_motion=self.on_motion)
                
    def on_center_map(self, *args):    
        scatter = self.ids.scatter
        scatter.scale = 1
        scatter.rotation = 0
        scatter.transform = Matrix().translate(self.pos[0], self.pos[1], 0)

    def add_option_buttons(self):
        self.append_option_button(IconButton(text=u'\uf096', on_press=self.on_center_map))
    
    def on_options(self, *args):
        self.show_customize_dialog()

    def _customized(self, instance):
        print('customized!' + str(instance))
        
    def show_customize_dialog(self):
        
        current_track_id = None if self.track == None else self.track.track_id 
        content = CustomizeMapView(settings=self.settings, 
                                   datastore=self.datastore, 
                                   track_manager=self.track_manager, 
                                   current_heat_channel = self.current_heat_channel,
                                   current_track_id = current_track_id)
        popup = Popup(title="Customize Track Map", content=content, size_hint=(0.7, 0.7))
        content.bind(on_customized=self._customized)
        content.bind(on_close=lambda *args:popup.dismiss())  
        popup.open()
                
    def on_optionsx(self):
        if self.heat_enabed:
            for source in self.sources.itervalues():
                self.remove_heat_values(source)
            self.heat_enabed = False
        else:
            for source in self.sources.itervalues():
                self.add_heat_values('TPS', source)
            self.heat_enabed = True
   
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
        if self.track_manager:
            point = GeoPoint.fromPoint(latitude, longitude)
            track = self.track_manager.find_nearby_track(point)
            if track != None:
                self.ids.track.setTrackPoints(track.map_points)
                self.track = track

    def remove_reference_mark(self, source):
        self.ids.track.remove_marker(source)

    def add_reference_mark(self, source, color):
        self.ids.track.add_marker(source, color)

    def update_reference_mark(self, source, point):
        self.ids.track.update_marker(str(source), point)

    def add_map_path(self, source_key, path, color):
        self.sources[str(source_key)] = source_key
        self.ids.track.add_path(str(source_key), path, color)

    def remove_map_path(self, source_key):
        self.ids.track.remove_path(str(source_key))
        self.sources.pop(str(source_key), None)

    def add_heat_values(self, channel, lap_ref):
        lap = lap_ref.lap
        session = lap_ref.session
        f = Filter().eq('LapCount', lap)
        dataset = self.datastore.query(sessions=[session], channels=[channel], data_filter=f)
        records = dataset.fetch_records()

        values = []
        for record in records:
            #pluck out just the channel value
            values.append(record[1])

        self.heat_values = values
        self.ids.track.add_heat_values(str(lap_ref), values)

    def remove_heat_values(self, lap_ref):
        self.ids.track.remove_heat_values(str(lap_ref))   
    
class BaseCustomizeMapView(Screen):
    def __init__(self, settings, datastore, track_manager, **kwargs):
        super(BaseCustomizeMapView, self).__init__(**kwargs)
        self.initialized = False
        self.settings = settings
        self.datastore = datastore
        self.track_manager = track_manager
        self.register_event_type('on_modified')
        
    def on_modified(self):
        pass
        
class HeatmapButton(LabelIconButton):
    pass

class TrackmapButton(LabelIconButton):
    pass

class CustomizeHeatmapView(BaseCustomizeMapView):
    available_channels = ListProperty()
    heatmap_channel = StringProperty(None)
    
    def __init__(self, settings, datastore, track_manager, **kwargs):
        super(CustomizeHeatmapView, self).__init__(settings, datastore, track_manager, **kwargs)
        self.heatmap_channel = kwargs.get('current_heatmap_channel')
        self.ids.heatmap_channel.bind(on_channel_selected=self.channel_selected)
    
    def on_enter(self):
        if self.initialized == False:
            channels = self._get_available_channel_names()
            self.available_channels = channels
            
    def _get_available_channel_names(self):
        available_channels = self.datastore.channel_list
        return [str(c) for c in available_channels]
        
    def on_available_channels(self, instance, value):
        self.ids.heatmap_channel.channels = value
        
    def channel_selected(self, instance, value):
        value = None if len(value) == 0 else value[0]
        modified = self.heatmap_channel != value
        if modified:
            self.dispatch('on_modified')
        
    def channel_cleared(self, *args):
        modified = self.heatmap_channel == None
        self.heatmap_channel = None
        if modified:
            self.dispatch('on_modified')
        
class CustomizeTrackView(BaseCustomizeMapView):
    track_id = StringProperty(None, allownone=True)
    def __init__(self, settings, datastore, track_manager, **kwargs):
        super(CustomizeTrackView, self).__init__(settings, datastore, track_manager, **kwargs)
        self.track = kwargs.get('current_track_id')
        self.ids.track_browser.set_trackmanager(track_manager)
        self.ids.track_browser.bind(on_track_selected=self.track_selected)
        self.ids.track_browser.init_view()
        
    def track_selected(self, instance, value):
        if type(value) is set:
            self.track_id = None if len(value) == 0 else next(iter(value))
        self.dispatch('on_modified')

class CustomizeMapView(BoxLayout):
    def __init__(self, settings, datastore, track_manager, **kwargs):
        super(CustomizeMapView, self).__init__(**kwargs)
        self._current_heatmap_channel = kwargs.get('current_heatmap_channel')
        self._current_track_id = kwargs.get('current_track_id')
        self.register_event_type('on_customized')
        self.register_event_type('on_close')
        
        screen_manager = self.ids.screens
        screen_manager.transition = SwapTransition()
        
        customize_heatmap_view = CustomizeHeatmapView(name='heat', settings=settings, datastore=datastore, track_manager=track_manager, current_heatmap_channel=self._current_heatmap_channel)
        customize_heatmap_view.bind(on_modified=self.on_modified)
                
        customize_track_view = CustomizeTrackView(name='track', settings=settings, datastore=datastore, track_manager=track_manager, current_track_id=self._current_track_id)
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
        
    def on_customized(self):
        pass
    
    def on_close(self):
        pass
    
    def confirm(self):
        self.dispatch('on_customized')
        self.dispatch('on_close')
    
    def cancel(self):
        self.dispatch('on_close')
        
    def on_modified(self, instance):
        self.ids.confirm.disabled = False
        
    def on_option(self, option):
        self.ids.screens.current = option
