#!/usr/bin/python
from autosportlabs.racecapture.tracks.trackmanager import TrackManager
import json
import zipfile
import StringIO
import os

tm = TrackManager()

tracks = tm.download_all_tracks()

mf = StringIO.StringIO()
with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    for track_id, track in tracks.iteritems():
        track_json_string = json.dumps(track.to_dict(), sort_keys=True, indent=2, separators=(',', ': '))
        zf.writestr('{}.json'.format(track_id), track_json_string)

default_tracks_archive_path = os.path.join('defaults', 'default_tracks.zip')

with open(default_tracks_archive_path, 'wb') as f:
    f.write(mf.getvalue())
