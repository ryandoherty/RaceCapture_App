import kivy
kivy.require('1.8.0')
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
import json
import sets
from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup
from autosportlabs.uix.track.trackmap import TrackMap
from autosportlabs.uix.track.racetrackview import RaceTrackView
from utils import *
from autosportlabs.racecapture.geo.geopoint import GeoPoint
Builder.load_file('autosportlabs/racecapture/views/tracks/tracksview.kv')

class SearchInput(TextInput):
    
    def __init__(self, *args, **kwargs):
        self.register_event_type('on_search')
        super(SearchInput, self).__init__(*args, **kwargs)
    
    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        if key in (9,13):
            self.dispatch('on_search')
        else:
            super(SearchInput, self)._keyboard_on_key_down(window, keycode, text, modifiers)
            
    def on_search(self, *args):
        pass
    
class TracksUpdateStatusView(BoxLayout):
    progressView = None
    messageView = None
    def __init__(self, **kwargs):
        super(TracksUpdateStatusView, self).__init__(**kwargs)
        self.progressView = self.ids.progress
        self.messageView = self.ids.updatemsg
        
    def _update_progress(self, percent):
        self.progressView.value = percent
    
    def _update_message(self, message):
        self.messageView.text = message
        
    def on_progress(self, count, total, message = None):
        progress_percent = (float(count) / float(total) * 100)
        Clock.schedule_once(lambda dt: self._update_progress(progress_percent))
        if message:
            Clock.schedule_once(lambda dt: self._update_message(message))
    
    def on_message(self, message):
        self.messageView.text = message

class TrackItemView(BoxLayout):
    track = None
    trackInfoView = None
    def __init__(self, **kwargs):
        super(TrackItemView, self).__init__(**kwargs)
        track = kwargs.get('track', None)
        trackInfoView = self.ids.trackinfo
        trackInfoView.setTrack(track)
        self.track = track
        self.trackInfoView = trackInfoView
        self.register_event_type('on_track_selected')
        
    def track_select(self, instance, value):
        self.dispatch('on_track_selected', value, self.track.trackId)
            
    def on_track_selected(self, selected, trackId):
        pass
    
    def setSelected(self, selected):
        self.ids.active = selected
        
class TrackInfoView(BoxLayout):
    track = None
    def __init__(self, **kwargs):
        super(TrackInfoView, self).__init__(**kwargs)
        
    def setTrack(self, track):
        if track:
            raceTrackView = self.ids.track
            raceTrackView.loadTrack(track)
            
            trackLabel = self.ids.name
            trackLabel.text = track.name
            
            trackConfigLabel = self.ids.configuration
            trackConfigLabel.text = 'Main Configuration' if not track.configuration else track.configuration 
            
            lengthLabel = self.ids.length
            lengthLabel.text = str(track.length) + ' mi.'
            
            flagImage = self.ids.flag
            cc = track.countryCode
            if cc:
                cc = cc.lower()
                try:
                    flagImagePath = 'resource/flags/' + str(track.countryCode.lower()) + '.png'
                    flagImage.sourceref = flagImagePath
                except Exception as detail:
                    print('Error loading flag for country code: ' + str(detail))  
            self.track = track
    
class TracksView(Screen):
    loaded = False
    
    def __init__(self, **kwargs):
        super(TracksView, self).__init__(**kwargs)
        self.trackManager = kwargs.get('trackManager')
        self.register_event_type('on_tracks_updated')
                
    def on_enter(self):
        if not self.loaded:
            self.ids.browser.init_view()
            self.loaded = True
            
    def on_tracks_updated(self, track_manager):
        self.ids.browser.set_trackmanager(track_manager)
    
    def check_for_update(self):
        self.ids.browser.on_update_check()
        
class TracksBrowser(BoxLayout):
    trackmap = None
    trackHeight = NumericProperty(dp(200))
    trackManager = None
    tracksUpdatePopup = None
    initialized = False
    tracksGrid = None
    selectedTrackIds = None
    def __init__(self, **kwargs):
        super(TracksBrowser, self).__init__(**kwargs)
        self.register_event_type('on_track_selected')
        self.selectedTrackIds = set()
         
    def set_trackmanager(self, track_manager):
        self.trackManager = track_manager
           
    def init_view(self):        
        self.initRegionsList()
        self.refreshTrackList()
        self.ids.namefilter.bind(on_search=self.on_search_track_name)
        self.initialized = True
        
    def setViewDisabled(self, disabled):
        self.ids.updatecheck.disabled = disabled
        self.ids.regions.disabled = disabled
        self.ids.namefilter.disabled = disabled
        self.ids.search.disabled = disabled
        if disabled == False and is_mobile_platform() == False:
            self.ids.namefilter.focus = True
    
    def dismissPopups(self):
        if self.tracksUpdatePopup:
            self.tracksUpdatePopup.dismiss()
         
    def loadAll(self, dt):
        self.initTracksList(self.trackManager.getTrackIdsInRegion())
                        
    def on_search_track_name(self, *args):
        if self.initialized:
            Clock.schedule_once(lambda dt: self.refreshTrackList())
                    
    def on_region_selected(self, instance, search):
        if self.initialized:
            Clock.schedule_once(lambda dt: self.refreshTrackList())

    def showProgressPopup(self, title, content):
        self.dismissPopups()
        if type(content) is str:
            content = Label(text=content)
        popup = Popup(title=title, content=content, auto_dismiss=False, size_hint=(None, None), size=(dp(400), dp(200)))
        popup.open()
        self.tracksUpdatePopup = popup
        
    def on_update_check_success(self):
        self.tracksUpdatePopup.content.on_message('Processing...')
        Clock.schedule_once(lambda dt: self.refreshTrackList())
        
    def on_update_check_error(self, details):
        self.dismissPopups() 
        Clock.schedule_once(lambda dt: self.refreshTrackList())
        print('Error updating: ' + str(details))       
        alertPopup('Error Updating', 'There was an error updating the track list.\n\nPlease check your network connection and try again')
        
    def on_update_check(self):
        self.setViewDisabled(True)
        tracksUpdateView = TracksUpdateStatusView()
        self.showProgressPopup('Checking for updates', tracksUpdateView)
        self.trackManager.updateAllTracks(tracksUpdateView.on_progress, self.on_update_check_success, self.on_update_check_error)
        
    def addNextTrack(self, index, keys):
        if index < len(keys):
            track = self.trackManager.tracks[keys[index]]
            trackView = TrackItemView(track=track)
            trackView.bind(on_track_selected=self.on_track_selected)
            trackView.size_hint_y = None
            trackView.height = self.trackHeight
            self.tracksGrid.add_widget(trackView)
            Clock.schedule_once(lambda dt: self.addNextTrack(index + 1, keys))
        else:
            self.dismissPopups()
            self.setViewDisabled(False)
        
    def refreshTrackList(self):
        region = self.ids.regions.text
        foundIds = self.trackManager.filterTracksByRegion(region)
        search = self.ids.namefilter.text
        if search != None and len(search) > 0:
            foundIds = self.trackManager.filterTracksByName(search, foundIds)
        self.initTracksList(foundIds)
        
    def initTracksList(self, trackIds = None):
        self.setViewDisabled(True)
        if trackIds == None:
            trackIds = self.trackManager.getAllTrackIds()
        trackCount = len(trackIds)
        grid = self.ids.tracksgrid
        grid.height = self.trackHeight * (trackCount + 1)
        grid.clear_widgets()
        self.tracksGrid = grid


        self.dismissPopups()
        if trackCount == 0:
            self.tracksGrid.add_widget(Label(text="No tracks found - try checking for updates"))
            self.setViewDisabled(False)            
            self.ids.namefilter.focus = True                        
        else:
            self.showProgressPopup("", "Loading")        
            self.addNextTrack(0, trackIds)
            
    def initRegionsList(self):
        regions = self.trackManager.regions
        regionsSpinner = self.ids.regions
        values = []
        for region in regions:
            name = region.name
            if regionsSpinner.text == '':
                regionsSpinner.text = name
            values.append(name)
        regionsSpinner.values = values
        
    def on_track_selected(self, instance, selected, trackId):
        if selected:
            self.selectedTrackIds.add(trackId)
        else:
            self.selectedTrackIds.discard(trackId)
            
    def selectAll(self, instance, value):
        if self.tracksGrid:
            for trackView in self.tracksGrid.children:
                trackView.setSelected(value)
