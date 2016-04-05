import kivy
kivy.require('1.9.1')

from kivy.properties import ObjectProperty
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.app import Builder
from helplabel import HelpLabel
from fieldlabel import FieldLabel
from settingsview import *
from utils import *
from valuefield import FloatValueField
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.tracks.tracksview import TrackInfoView, TracksView
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.uix.toast.kivytoast import toast
from autosportlabs.widgets.scrollcontainer import ScrollContainer

TRACK_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/trackconfigview.kv'

GPS_STATUS_POLL_INTERVAL = 1.0
GPS_NOT_LOCKED_COLOR = [0.7, 0.7, 0.0, 1.0]
GPS_LOCKED_COLOR = [0.0, 1.0, 0.0, 1.0]

class SectorPointView(BoxLayout):
    databus = None
    point = None
    def __init__(self, **kwargs):
        super(SectorPointView, self).__init__(**kwargs)
        self.databus = kwargs.get('databus')
        self.register_event_type('on_config_changed')
        title = kwargs.get('title', None)
        if title:
            self.setTitle(title)
        Clock.schedule_interval(lambda dt: self.update_gps_status(), GPS_STATUS_POLL_INTERVAL)

    def _get_gps_quality(self):
        gps_quality = self.databus.channel_data.get('GPSQual')
        return 0 if gps_quality is None else int(gps_quality)
    
    def update_gps_status(self, *args):
        gps_quality = self._get_gps_quality()
        self.ids.gps_target.color = GPS_NOT_LOCKED_COLOR if gps_quality < GpsConfig.GPS_QUALITY_2D else GPS_LOCKED_COLOR
            
    def on_config_changed(self):
        pass
        
    def setTitle(self, title):
        kvFind(self, 'rcid', 'title').text = title
        
    def on_update_target(self, *args):
        try:
            if self._get_gps_quality() >= GpsConfig.GPS_QUALITY_2D:
                channel_data = self.databus.channel_data
                point = self.point
                point.latitude = channel_data.get('Latitude')
                point.longitude = channel_data.get('Longitude') 
                self._refresh_point_view()
                self.dispatch('on_config_changed')
                toast('Target updated')
            else:
                toast('No GPS Fix', True)
        except Exception as e:
            toast('Error reading GPS target')
        
    def _on_edited(self, instance, value):
        self.set_point(value)
        self.dispatch('on_config_changed')
    
    def on_customize(self, *args):
        if self.point:
            content = GeoPointEditor(point=self.point, databus=self.databus)
            popup = Popup(title = 'Edit Track Target',
                          content = content, 
                          size_hint=(None, None), size = (dp(500), dp(220)))
            content.bind(on_close=lambda *args:popup.dismiss())                     
            content.bind(on_point_edited=self._on_edited)
            popup.open()
        
    def _refresh_point_view(self):
        self.ids.lat.text = str(self.point.latitude)
        self.ids.lon.text = str(self.point.longitude)
        
    def set_point(self, point):
        self.point = point
        self._refresh_point_view()
            
class GeoPointEditor(BoxLayout):
    def __init__(self, point, databus, **kwargs):
        super(GeoPointEditor, self).__init__(**kwargs)
        self.point = point
        self.databus = databus
        self.register_event_type('on_point_edited')
        self.register_event_type('on_close')
        self._refresh_view(self.point.latitude, self.point.longitude)
        self.ids.lat.set_next(self.ids.lon)
        self.ids.lon.set_next(self.ids.lat)
        Clock.schedule_interval(self.update_gps_status, GPS_STATUS_POLL_INTERVAL)
        
    def on_latitude(self, instance, value):
        pass
        
    def on_longitude(self, instance, value):
        pass
        
    def _refresh_view(self, latitude, longitude):
        self.ids.lat.text = str(latitude)
        self.ids.lon.text = str(longitude)
    
    def on_point_edited(self, *args):
        pass
    
    def on_close(self, *args):
        pass
    
    def on_paste_point(self, *args):
        try:
            point_string = Clipboard.get('UTF8_STRING')
            lat_lon = point_string.split(",")
            lat = float(lat_lon[0])
            lon = float(lat_lon[1])
            self.ids.lat.text = str(lat)
            self.ids.lon.text = str(lon)
        except Exception:
            toast('Required format is: Latitude, Longitude\nin NN.NNNNN decimal format', True)

    def update_gps_status(self, dt,  *args):
        gps_quality = self._get_gps_quality()
        self.ids.gps_target.color = GPS_NOT_LOCKED_COLOR if gps_quality < GpsConfig.GPS_QUALITY_2D else GPS_LOCKED_COLOR
            
    def _get_gps_quality(self):
        gps_quality = self.databus.channel_data.get('GPSQual')
        return 0 if gps_quality is None else int(gps_quality)

    def on_update_target(self, *args):
        try:
            if self._get_gps_quality() >= GpsConfig.GPS_QUALITY_2D:
                channel_data = self.databus.channel_data
                self._refresh_view(channel_data.get('Latitude'), channel_data.get('Longitude'))
            else:
                toast('No GPS Fix', True)
        except Exception:
            toast('Error reading GPS target')
    
    def close(self):
        Clock.unschedule(self.update_gps_status)              
        point = self.point
        try:
            point.latitude = float(self.ids.lat.text)
            point.longitude = float(self.ids.lon.text)
            self.dispatch('on_point_edited', self.point)
        except Exception:
            toast('NN.NNNNN decimal latitude/longitude format required', True)
        self.dispatch('on_close')

            
class EmptyTrackDbView(BoxLayout):
    def __init__(self, **kwargs):
        super(EmptyTrackDbView, self).__init__(**kwargs)
        
class TrackDbItemView(BoxLayout):
    track = None
    trackInfoView = None
    index = 0
    def __init__(self, **kwargs):
        super(TrackDbItemView, self).__init__(**kwargs)
        track = kwargs.get('track', None)
        self.index = kwargs.get('index', 0)
        trackInfoView = kvFind(self, 'rcid', 'trackinfo')
        trackInfoView.setTrack(track)
        self.track = track
        self.trackInfoView = trackInfoView
        self.register_event_type('on_remove_track')

    def on_remove_track(self, index):
        pass
    
    def removeTrack(self):
        self.dispatch('on_remove_track', self.index)
        
class TrackSelectionPopup(BoxLayout):
    track_browser = None
    def __init__(self, **kwargs):
        super(TrackSelectionPopup, self).__init__(**kwargs)
        self.register_event_type('on_tracks_selected')
        track_manager = kwargs.get('track_manager', None)
        track_browser = kvFind(self, 'rcid', 'browser')
        track_browser.set_trackmanager(track_manager)
        track_browser.init_view()
        self.track_browser = track_browser
        
    def on_tracks_selected(self, selectedTrackIds):
        pass
    
    def confirmAddTracks(self):
        self.dispatch('on_tracks_selected', self.track_browser.selectedTrackIds)        
        
            
class AutomaticTrackConfigScreen(Screen):
    trackDb = None
    tracksGrid = None
    track_manager = ObjectProperty(None)
    TRACK_ITEM_MIN_HEIGHT = 200
    trackSelectionPopup = None
    def __init__(self, **kwargs):
        super(AutomaticTrackConfigScreen, self).__init__(**kwargs)
        self.tracksGrid = kvFind(self, 'rcid', 'tracksgrid')
        self.register_event_type('on_tracks_selected')
        self.register_event_type('on_modified')
                        
    def on_modified(self, *args):
        pass
                
    def on_config_updated(self, rcpCfg):
        self.trackDb = rcpCfg.trackDb
        self.init_tracks_list()
        
    def on_track_manager(self, instance, value):
        self.track_manager = value
        self.init_tracks_list()
    
    def on_tracks_selected(self, instance, selectedTrackIds):
        if self.trackDb:
            failures = False
            for trackId in selectedTrackIds:
                trackMap = self.track_manager.get_track_by_id(trackId)
                if trackMap:
                    startFinish = trackMap.start_finish_point
                    if startFinish and startFinish.latitude and startFinish.longitude:
                        Logger.info("TrackConfigView:  adding track " + str(trackMap))
                        track = Track.fromTrackMap(trackMap)
                        self.trackDb.tracks.append(track)
                    else:
                        failures = True
            if failures:
                alertPopup('Cannot Add Tracks', 'One or more tracks could not be added due to missing start/finish points.\n\nPlease check for track map updates and try again.')            
            self.init_tracks_list()
            self.trackSelectionPopup.dismiss()
            self.trackDb.stale = True
            self.dispatch('on_modified')
                    
    def on_add_track_db(self):
        trackSelectionPopup = TrackSelectionPopup(track_manager=self.track_manager)
        popup = Popup(title = 'Add Race Tracks', content = trackSelectionPopup, size_hint=(0.9, 0.9))
        trackSelectionPopup.bind(on_tracks_selected=self.on_tracks_selected)
        popup.open()
        self.trackSelectionPopup = popup
    
    def init_tracks_list(self):
        if self.track_manager and self.trackDb:
            matchedTracks = []
            for track in self.trackDb.tracks:
                matchedTrack = self.track_manager.find_track_by_short_id(track.trackId)
                if matchedTrack:
                    matchedTracks.append(matchedTrack)
                    
            grid = kvFind(self, 'rcid', 'tracksgrid')
            grid.clear_widgets()
            if len(matchedTracks) == 0:
                grid.add_widget(EmptyTrackDbView())
                self.tracksGrid.height = dp(self.TRACK_ITEM_MIN_HEIGHT)
            else:
                self.tracksGrid.height = dp(self.TRACK_ITEM_MIN_HEIGHT) * (len(matchedTracks) + 1)
                index = 0
                for track in matchedTracks:
                    trackDbView = TrackDbItemView(track=track, index=index)
                    trackDbView.bind(on_remove_track=self.on_remove_track)
                    trackDbView.size_hint_y = None
                    trackDbView.height = dp(self.TRACK_ITEM_MIN_HEIGHT)
                    grid.add_widget(trackDbView)
                    index += 1
                
            self.disableView(False)
            
    def on_remove_track(self, instance, index):
            try:
                del self.trackDb.tracks[index]
                self.init_tracks_list()
                self.trackDb.stale = True
                self.dispatch('on_modified')
                            
            except Exception as detail:
                print('Error removing track from list ' + str(detail))
                    
    def disableView(self, disabled):
        kvFind(self, 'rcid', 'addtrack').disabled = disabled
        
class ManualTrackConfigScreen(Screen):
    trackCfg = None
    sectorViews = []
    startLineView = None
    finishLineView = None
    separateStartFinish = False
    _databus = None

    def __init__(self, **kwargs):
        super(ManualTrackConfigScreen, self).__init__(**kwargs)
        self._databus = kwargs.get('databus')
        sepStartFinish = kvFind(self, 'rcid', 'sepStartFinish') 
        sepStartFinish.bind(on_setting=self.on_separate_start_finish)
        sepStartFinish.setControl(SettingsSwitch())
        
        self.startLineView = self.ids.start_line
        self.startLineView.databus = self._databus
        self.finishLineView = self.ids.finish_line
        self.finishLineView.databus = self._databus
        
        self.separateStartFinish = False
        sectorsContainer = self.ids.sectors_grid        
        self.sectorsContainer = sectorsContainer
        self.initSectorViews()
            
        sectorsContainer.height = dp(35) * CONFIG_SECTOR_COUNT
        sectorsContainer.size_hint = (1.0, None)
        
        self.register_event_type('on_modified')
                        
    def on_modified(self, *args):
        pass
    
    def on_separate_start_finish(self, instance, value):        
        if self.trackCfg:
            self.trackCfg.track.trackType = 1 if value else 0
            self.trackCfg.stale = True
            self.dispatch('on_modified')            
            self.separateStartFinish = value
            self.updateTrackViewState()
              
    def initSectorViews(self):
        
        sectorsContainer = self.sectorsContainer
        sectorsContainer.clear_widgets()
        
        self.startLineView.bind(on_config_changed=self.on_config_changed)
        self.finishLineView.bind(on_config_changed=self.on_config_changed)
                                
        self.updateTrackViewState()
            
    def on_config_changed(self, *args):
        self.trackCfg.stale = True
        self.dispatch('on_modified')
                    
    def updateTrackViewState(self):
        if not self.separateStartFinish:
            self.startLineView.setTitle('Start / Finish')
            self.finishLineView.setTitle('- - -')            
            self.finishLineView.disabled = True
        else:
            self.startLineView.setTitle('Start Line')
            self.finishLineView.setTitle('Finish Line')
            self.finishLineView.disabled = False
            
    def on_config_updated(self, rcpCfg):
        trackCfg = rcpCfg.trackConfig
        
        separateStartFinishSwitch = kvFind(self, 'rcid', 'sepStartFinish')
        self.separateStartFinish = trackCfg.track.trackType == TRACK_TYPE_STAGE
        separateStartFinishSwitch.setValue(self.separateStartFinish) 
        
        sectorsContainer = self.sectorsContainer

        sectorsContainer.clear_widgets()
        for i in range(0, len(trackCfg.track.sectors)):
            sectorView = SectorPointView(title = 'Sector ' + str(i), databus=self._databus)
            sectorView.bind(on_config_changed=self.on_config_changed)
            sectorsContainer.add_widget(sectorView)
            sectorView.set_point(trackCfg.track.sectors[i])
            self.sectorViews.append(sectorView)

        self.startLineView.set_point(trackCfg.track.startLine)
        self.finishLineView.set_point(trackCfg.track.finishLine)
        
        self.trackCfg = trackCfg
        self.updateTrackViewState()
            
class TrackConfigView(BaseConfigView):
    trackCfg = None
    trackDb = None
    
    screenManager = None
    manualTrackConfigView = None
    autoConfigView = None
    _databus = None
    
    def __init__(self, **kwargs):
        Builder.load_file(TRACK_CONFIG_VIEW_KV)
        super(TrackConfigView, self).__init__(**kwargs)
        self._databus = kwargs.get('databus')
        self.register_event_type('on_config_updated')
        
        self.manualTrackConfigView = ManualTrackConfigScreen(name='manual', databus=self._databus)
        self.manualTrackConfigView.bind(on_modified=self.on_modified)
        
        self.autoConfigView = AutomaticTrackConfigScreen(name='auto')
        self.autoConfigView.bind(on_modified=self.on_modified)
        
        screenMgr = kvFind(self, 'rcid', 'screenmgr')
        screenMgr.add_widget(self.manualTrackConfigView)
        self.screenManager = screenMgr
        
        autoDetect = kvFind(self, 'rcid', 'autoDetect')
        autoDetect.bind(on_setting=self.on_auto_detect)
        autoDetect.setControl(SettingsSwitch())
        
        self.autoConfigView.track_manager = kwargs.get('track_manager')

    def on_tracks_updated(self, track_manager):
        self.autoConfigView.track_manager = track_manager
        
    def on_config_updated(self, rcpCfg):
        trackCfg = rcpCfg.trackConfig
        trackDb = rcpCfg.trackDb
        
        autoDetectSwitch = kvFind(self, 'rcid', 'autoDetect')
        autoDetectSwitch.setValue(trackCfg.autoDetect)
        
        self.manualTrackConfigView.on_config_updated(rcpCfg)
        self.autoConfigView.on_config_updated(rcpCfg)
        self.trackCfg = trackCfg
        self.trackDb = trackDb
        
    def on_auto_detect(self, instance, value):
        if value:
            self.screenManager.switch_to(self.autoConfigView)
        else:
            self.screenManager.switch_to(self.manualTrackConfigView)

        if self.trackCfg:
            self.trackCfg.autoDetect = value
            self.trackCfg.stale = True
            self.dispatch('on_modified')
            
            
