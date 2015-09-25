import json
import time
import copy
import errno
import string
import logging
from threading import Thread, Lock
from urlparse import urljoin, urlparse
import urllib2
import os
import traceback
from autosportlabs.racecapture.geo.geopoint import GeoPoint, Region
from kivy.logger import Logger
from utils import time_to_epoch

class TrackMap:

    def __init__(self, **kwargs):
        self.map_points = []
        self.sector_points = []
        self.name = ''
        self.created = None
        self.updated = None
        self.length = 0
        self.track_id = None
        self.start_finish_point = None
        self.finish_point = None
        self.country_code = None
        self.configuration = None

    @property
    def centerpoint(self):
        if len(self.map_points) > 0:
            return self.map_points[0]
        return None

    @property
    def short_id(self):
        short_id = 0
        if self.created is not None:
            try:
                short_id = time_to_epoch(self.created)
            except:
                pass
        return short_id

    def from_dict(self, venue):

        self.start_finish_point = GeoPoint.fromPointJson(venue.get('start_finish'))
        self.finish_point = GeoPoint.fromPointJson(venue.get('finish'))
        self.country_code = venue.get('country_code', self.country_code)
        self.created = venue.get('created', self.created)
        self.updated = venue.get('updated', self.updated)
        self.name = venue.get('name', self.name)
        self.configuration = venue.get('configuration', self.configuration)
        self.length = venue.get('length', self.length)
        self.track_id = venue.get('id')

        map_points_array = venue.get('track_map_array')

        if map_points_array:
            for point in map_points_array:
                self.map_points.append(GeoPoint.fromPoint(point[0], point[1]))

        sector_array = venue.get('sector_points')

        if sector_array:
            for point in sector_array:
                self.sector_points.append(GeoPoint.fromPoint(point[0], point[1]))

        if not self.short_id > 0:
            raise Warning("Could not parse trackMap: short_id is invalid")
    
    def to_dict(self):
        venue = {'sector_points': [], 'track_map_array': []}

        if self.start_finish_point:
            venue['start_finish'] = self.start_finish_point.toJson()

        if self.finish_point:
            venue['finish'] = self.finish_point.toJson()

        venue['country_code'] = self.country_code
        venue['created'] = self.created
        venue['updated'] = self.updated
        venue['name'] = self.name
        venue['configuration'] = self.configuration
        venue['length'] = self.length
        venue['id'] = self.track_id

        for point in self.map_points:
            venue['track_map_array'].append([point.latitude, point.longitude])

        for point in self.sector_points:
            venue['sector_points'].append([point.latitude, point.longitude])

        return venue

class TrackManager:
    updateLock = None
    tracks_user_dir = '.'
    track_user_subdir = '/venues'
    on_progress = lambda self, value: value
    rcp_venue_url = 'https://race-capture.com/api/v1/venues'
    readRetries = 3
    retryDelay = 1.0
    tracks = None
    regions = None
    trackIdsInRegion = None
    base_dir = None

    def __init__(self, **kwargs):
        self.set_tracks_user_dir(kwargs.get('user_dir', self.tracks_user_dir) + self.track_user_subdir)
        self.updateLock = Lock()
        self.regions = []
        self.tracks = {}
        self.trackIdsInRegion = []
        self.base_dir = kwargs.get('base_dir')
        
    def set_tracks_user_dir(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        self.tracks_user_dir = path
        
    def init(self, progressCallback, winCallback, failCallback):
        self.loadRegions()
        self.loadCurrentTracks(progressCallback, winCallback, failCallback)
        
    def loadRegions(self):
        del(self.regions[:])
        try:
            regionsJson = json.load(open(os.path.join(self.base_dir, 'resource', 'settings', 'geo_regions.json')))
            regionsNode = regionsJson.get('regions')
            if regionsNode:
                for regionNode in regionsNode: 
                    region = Region()
                    region.fromJson(regionNode)
                    self.regions.append(region)
        except Exception as detail:
            Logger.warning('TrackManager: Error loading regions data ' + traceback.format_exc())

    @property
    def track_ids(self):
        return self.tracks.keys()
    
    def getTrackIdsInRegion(self):
        return self.trackIdsInRegion
        
    def findTrackByShortId(self, id):
        for track in self.tracks.itervalues():
            if id == track.short_id:
                return track
        return None
        
    def findNearbyTrack(self, point, searchRadius):
        for trackId in self.tracks.keys():
            track = self.tracks[trackId]
            track_center = track.centerpoint
            if track_center and track_center.withinCircle(point, searchRadius):
                return track
        return None
        
    def filterTracksByName(self, name, trackIds=None):
        if trackIds == None:
            trackIds = self.tracks.keys()
        filteredTrackIds = []
        for trackId in trackIds:
            trackName = self.tracks[trackId].name
            if string.lower(name.strip()) in string.lower(trackName.strip()):
                filteredTrackIds.append(trackId)
        return filteredTrackIds
                
    def filterTracksByRegion(self, regionName):
        allTrackIds = self.tracks.keys()
        trackIdsInRegion = self.trackIdsInRegion
        del trackIdsInRegion[:]
        
        if regionName == None:
            trackIdsInRegion.extend(allTrackIds)
        else:
            for region in self.regions:
                if region.name == regionName:
                    if len(region.points) > 0:
                        for trackId in allTrackIds:
                            track = self.tracks[trackId]
                            if region.withinRegion(track.centerpoint):
                                trackIdsInRegion.append(trackId)
                    else:
                        trackIdsInRegion.extend(allTrackIds)
                    break
        return trackIdsInRegion

    def getTrackById(self, trackId):
        return self.tracks.get(trackId)
    
    def load_json(self, uri):
        retries = 0
        while retries < self.readRetries:
            try:
                opener = urllib2.build_opener()
                opener.addheaders = [('Accept', 'application/json')]
                jsonStr = opener.open(uri).read()
                j = json.loads(jsonStr)
                return j
            except Exception as detail:
                Logger.warning('TrackManager: Failed to read: from {} : {}'.format(uri, traceback.format_exc()))
                if retries < self.readRetries:
                    Logger.warning('TrackManager: retrying in ' + str(self.retryDelay) + ' seconds...')
                    retries += 1
                    time.sleep(self.retryDelay)
        raise Exception('Error reading json doc from: ' + uri)

    def download_all_tracks(self):
        tracks = {}
        venues = self.fetch_venue_list(True)

        for venue in venues:
                track = TrackMap()
                track.from_dict(venue)
                tracks[track.track_id] = track

        return tracks

    def fetch_venue_list(self, full_response=False):
        start = 0
        per_page = 100
        total_venues = None
        next_uri = self.rcp_venue_url + '?start=' + str(start) + '&per_page=' + str(per_page)

        if full_response:
            next_uri += '&expand=1'

        venues_list = []

        while next_uri:
            response = self.load_json(next_uri)
            try:
                if total_venues is None:
                    total_venues = int(response.get('total', None))
                    if total_venues is None:
                        raise MissingKeyException('Venue list JSON: could not get total venue count')

                venues = response.get('venues', None)

                if venues is None:
                    raise MissingKeyException('Venue list JSON: could not get venue list')

                venues_list += venues
                next_uri = response.get('nextURI')

            except MissingKeyException as detail:
                Logger.error('TrackManager: Malformed venue JSON from url ' + nextUri + '; json =  ' + str(response) +
                             ' ' + str(detail))
                
        Logger.info('TrackManager: fetched list of ' + str(len(venues_list)) + ' tracks')

        if not total_venues == len(venues_list):
            Logger.warning('TrackManager: track list count does not reflect downloaded track list size ' + str(total_venues) + '/' + str(len(venues_list)))

        return venues_list

    def download_track(self, venueId):
        trackUrl = self.rcp_venue_url + '/' + venueId
        response = self.load_json(trackUrl)
        trackMap = TrackMap()
        try:
            track_json = response.get('venue')
            trackMap.from_dict(track_json)
            return copy.deepcopy(trackMap)
        except Warning:
            return None
        
    def saveTrack(self, track):
        path = self.tracks_user_dir + '/' + track.track_id + '.json'
        trackJsonString = json.dumps(track.to_dict(), sort_keys=True, indent=2, separators=(',', ': '))
        with open(path, 'w') as text_file:
            text_file.write(trackJsonString)
    
    def loadCurrentTracksWorker(self, winCallback, failCallback, progressCallback=None):
        try:
            self.updateLock.acquire()
            self.loadCurrentTracks(progressCallback)
            winCallback()
        except Exception as detail:
            logging.exception('')
            failCallback(detail)
        finally:
            self.updateLock.release()
        
    def loadCurrentTracks(self, progressCallback=None, winCallback=None, failCallback=None):
        if winCallback and failCallback:
            t = Thread(target=self.loadCurrentTracksWorker, args=(winCallback, failCallback, progressCallback))
            t.daemon = True
            t.start()
        else:
            existingTracksFilenames = os.listdir(self.tracks_user_dir)
            self.tracks.clear()
            track_count = len(existingTracksFilenames)
            count = 0

            for trackPath in existingTracksFilenames:
                try:
                    json_data = open(self.tracks_user_dir + '/' + trackPath)
                    track_dict = json.load(json_data)

                    if track_dict is not None:
                        track = TrackMap()
                        track.from_dict(track_dict)

                        self.tracks[track.track_id] = track
                        count += 1
                        if progressCallback:
                            progressCallback(count, track_count, track.name)
                except Exception as detail:
                    Logger.warning('TrackManager: failed to read track file ' + trackPath + ';\n' + str(detail))

            del self.trackIdsInRegion[:]
            self.trackIdsInRegion.extend(self.tracks.keys())
                        
    def updateAllTracksWorker(self, winCallback, failCallback, progressCallback=None):
        try:
            self.updateLock.acquire()
            self.refresh(progressCallback)
            winCallback()
        except Exception as detail:
            logging.exception('')
            failCallback(detail)
        finally:
            self.updateLock.release()
            
    def refresh(self, progress_cb=None, success_cb=None, fail_cb=None):
        if success_cb and fail_cb:
            t = Thread(target=self.updateAllTracksWorker, args=(success_cb, fail_cb, progress_cb))
            t.daemon = True
            t.start()
        else:
            if len(self.tracks) == 0:
                Logger.info("TrackManager: No tracks found locally, fetching all tracks")
                track_list = self.download_all_tracks()
                count = 0
                total = len(track_list)

                for track_id, track in track_list.iteritems():
                    count += 1
                    if progress_cb:
                        progress_cb(count, total, track.name)
                    self.saveTrack(track)
                    self.tracks[track_id] = track
            else:
                Logger.info("TrackManager: refreshing tracks")
                venues = self.fetch_venue_list()

                track_count = len(venues)
                count = 0

                for venue in venues:
                    update = False
                    count += 1
                    venue_id = venue.get('id')

                    if self.tracks.get(venue_id) is None:
                        Logger.info('TrackManager: new track detected ' + venue.name)
                        update = True
                    elif not self.tracks[venue_id].updated == venue['updated']:
                        Logger.info('TrackManager: existing map changed ' + venue_id)
                        update = True

                    if update:
                        updated_track = self.download_track(venue_id)
                        if updated_track is not None:
                            self.saveTrack(updated_track, venue_id)
                            self.tracks[venue_id] = updated_track
                            if progress_cb:
                                progress_cb(count, track_count, updated_track.name)
                    else:
                        progress_cb(count, track_count)

class MissingKeyException(Exception):
    pass
