import kivy
from autosportlabs.racecapture.theme.color import ColorScheme
from kivy.uix.behaviors import ToggleButtonBehavior
kivy.require('1.9.1')
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.logger import Logger
from kivy.core.window import Window
import json
import sets
from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup
from autosportlabs.uix.track.trackmap import TrackMapView
from autosportlabs.uix.track.racetrackview import RaceTrackView
from utils import *
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from iconbutton import LabelIconButton
from autosportlabs.widgets.scrollcontainer import ScrollContainer

Builder.load_file('autosportlabs/racecapture/views/tracks/tracksview.kv')

class SearchInput(TextInput):

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_search')
        super(SearchInput, self).__init__(*args, **kwargs)

    def on_text_validate(self, *args):
        self.dispatch('on_search')

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

    def on_progress(self, count=None, total=None, message=None):
        if count and total:
            progress_percent = (float(count) / float(total) * 100)
            Clock.schedule_once(lambda dt: self._update_progress(progress_percent))
        if message:
            Clock.schedule_once(lambda dt: self._update_message(message))

    def on_message(self, message):
        self.messageView.text = message



class BaseTrackItemView(BoxLayout):
    track = None
    trackInfoView = None
    def __init__(self, **kwargs):
        super(BaseTrackItemView, self).__init__(**kwargs)
        track = kwargs.get('track', None)
        trackInfoView = self.ids.trackinfo
        trackInfoView.setTrack(track)
        self.track = track
        self.trackInfoView = trackInfoView
        self.register_event_type('on_track_selected')

    def on_track_selected(self, selected, trackId):
        pass

class TrackItemView(BaseTrackItemView):
    def track_select(self, instance, value):
        self.dispatch('on_track_selected', value, self.track.track_id)

    def setSelected(self, selected):
        self.ids.active = selected

class SingleTrackItemView(ToggleButtonBehavior, BaseTrackItemView):
    selected_color = ListProperty(ColorScheme.get_dark_background())

    def on_state(self, instance, value):
        selected = value == 'down'
        self.selected_color = ColorScheme.get_medium_background() if selected else ColorScheme.get_dark_background()
        self.dispatch('on_track_selected', selected, self.track.track_id)

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
            cc = track.country_code
            if cc:
                cc = cc.lower()
                try:
                    flagImagePath = 'resource/flags/' + str(track.country_code.lower()) + '.png'
                    flagImage.source = flagImagePath
                except Exception as detail:
                    print('Error loading flag for country code: ' + str(detail))
            self.track = track

class TracksView(Screen):
    loaded = False
    track_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(TracksView, self).__init__(**kwargs)
        self.track_manager = kwargs.get('track_manager')
        self.register_event_type('on_tracks_updated')

    def init_browser(self):
        self.ids.browser.set_trackmanager(self.track_manager)
        self.ids.browser.init_view()

    def on_track_manager(self, instance, value):
        if value:
            Clock.schedule_once(lambda dt: self.init_browser())

    def on_enter(self):
        if not self.loaded:
            self.loaded = True

    def on_tracks_updated(self, track_manager):
        self.track_manager = track_manager

    def check_for_update(self):
        self.ids.browser.on_update_check()

class TracksBrowser(BoxLayout):
    multi_select = BooleanProperty(True)
    trackmap = None
    trackHeight = NumericProperty(dp(200))
    trackManager = None
    tracksUpdatePopup = None
    initialized = False
    tracksGrid = None
    selectedTrackIds = None
    tracks_loading = False
    last_scroll_y = 1.0
    INITIAL_DISPLAY_LIMIT = 10
    LAZY_DISPLAY_CHUNK_COUNT = 1
    LOOK_AHEAD_TRACKS = 10
    TRACK_HEIGHT_PADDING = dp(10)

    def __init__(self, **kwargs):
        super(TracksBrowser, self).__init__(**kwargs)
        self.register_event_type('on_track_selected')
        self.selectedTrackIds = set()

    def on_track_selected(self, value):
        pass

    def on_scroll(self, instance, value):
        scroll_y = self.ids.scrltracks.scroll_y
        last_scroll_y = self.last_scroll_y
        self.last_scroll_y = scroll_y
        # only check to lazy load if we're scrolling towards the bottom
        if  scroll_y < last_scroll_y:
            self.lazy_load_more_maybe()

    def lazy_load_more_maybe(self):
        sb = self.ids.scrltracks
        current_index = self.load_limit
        tracks_count = len(self.current_track_ids)
        current_pct_loaded = 1.0 - (float(current_index - self.LOOK_AHEAD_TRACKS) / float(tracks_count))
        if sb.scroll_y < current_pct_loaded and current_index < tracks_count:
            if not self.tracks_loading:
                new_load_limit = current_index + self.LAZY_DISPLAY_CHUNK_COUNT
                if new_load_limit > tracks_count:
                    new_load_limit = tracks_count
                self.load_limit = new_load_limit
                self.tracks_loading = True
                self.addNextTrack(current_index, self.current_track_ids)
            Clock.schedule_once(lambda dt: self.lazy_load_more_maybe(), 1.0)

    def on_multi_select(self, instance, value):
        if value == False:
            selectall = self.ids.selectall_option
            selectall.parent.remove_widget(selectall)

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
        self.initTracksList(self.trackManager.get_track_ids_in_region())

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
        self.trackManager.refresh(tracksUpdateView.on_progress, self.on_update_check_success, self.on_update_check_error)

    def addNextTrack(self, index, keys):
        if index < self.load_limit:
            track = self.trackManager.tracks[keys[index]]

            trackView = TrackItemView(track=track) if self.multi_select == True else SingleTrackItemView(track=track)
            trackView.bind(on_track_selected=self.track_selected)
            trackView.size_hint_y = None
            trackView.height = self.trackHeight
            self.tracksGrid.add_widget(trackView)
            Clock.schedule_once(lambda dt: self.addNextTrack(index + 1, keys), 0.1)
        else:
            self.dismissPopups()
            self.setViewDisabled(False)
            self.last_scroll_y = self.ids.scrltracks.scroll_y
            self.tracks_loading = False

    def refreshTrackList(self):
        region = self.ids.regions.text
        foundIds = self.trackManager.filter_tracks_by_region(region)
        search = self.ids.namefilter.text
        if search != None and len(search) > 0:
            foundIds = self.trackManager.filter_tracks_by_name(search, foundIds)
        self.initTracksList(foundIds)

    def initTracksList(self, track_ids=None):
        self.setViewDisabled(True)
        if track_ids is None:
            track_ids = self.trackManager.track_ids
        track_count = len(track_ids)
        grid = self.ids.tracksgrid
        grid.clear_widgets()
        self.tracksGrid = grid
        self.ids.tracksgrid.height = ((track_count) * (self.trackHeight + self.TRACK_HEIGHT_PADDING))
        self.ids.scrltracks.height = 0
        self.ids.scrltracks.scroll_y = 1.0
        self.last_scroll_y = 1.0
        self.loading = False

        self.dismissPopups()
        if track_count == 0:
            Logger.info("TracksViews: no tracks")
            self.tracksGrid.add_widget(Label(text="No tracks found - try checking for updates"))
            self.setViewDisabled(False)
            self.ids.namefilter.focus = True
        else:
            self.load_limit = self.INITIAL_DISPLAY_LIMIT if len(track_ids) > self.INITIAL_DISPLAY_LIMIT else len(track_ids)
            self.current_track_ids = track_ids
            self.addNextTrack(0, track_ids)
            self.tracks_loading = True

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

    def track_selected(self, instance, selected, trackId):
        if selected:
            self.selectedTrackIds.add(trackId)
        else:
            self.selectedTrackIds.discard(trackId)
        self.dispatch('on_track_selected', self.selectedTrackIds)

    def selectAll(self, instance, value):
        if self.tracksGrid:
            for trackView in self.tracksGrid.children:
                trackView.setSelected(value)
