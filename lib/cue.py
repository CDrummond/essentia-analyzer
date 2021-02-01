#
# Analyse files with Essentia
#
# Copyright (c) 2020-2021 Craig Drummond <craig.p.drummond@gmail.com>
# GPLv3 license.
#

import logging
import os
import sqlite3
import subprocess
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

CUE_TRACK = '.CUE_TRACK.'
_LOGGER = logging.getLogger(__name__)

def get_cue_tracks(lms_db, lms_path, path, essentia_root_len, tmp_path):
    tracks=[]
    if lms_db is not None:
        _LOGGER.debug('Reading CUE metadata for %s' % path[essentia_root_len:])
        # Convert essentia path into LMS path...
        lms_full_path = '%s%s' % (lms_path, path[essentia_root_len:])
        # Get list of cue tracks from LMS db...
        cursor = lms_db.execute("select url, title, id, album, secs from tracks where url like '%%%s#%%'" % quote(lms_full_path))
        for row in cursor:
            parts=row[0].split('#')
            if 2==len(parts):
                times=parts[1].split('-')
                if 2==len(times):
                    track_artist=None
                    album_artist=None
                    album_name=None
                    contributors = lms_db.execute("select contributor, role from contributor_track where track=?", (row[2],)).fetchall()
                    genres = lms_db.execute("select genre from genre_track where track=?", (row[2],)).fetchall()
                    album = lms_db.execute("select title from albums where id=?", (row[3],)).fetchone()
                    genre_list = []
                    if albums is not None:
                        album_name = album[0]
                    if genres is not None:
                        for g in genres:
                            genre = lms_db.execute("select name from genres where id=?", (g[0],)).fetchone()
                            if genre is not None:
                                genre_list.append(genre[0])
                    if contributors is not None:
                        for cont in contributors:
                            if track_artist is None and(1 == cont[1] or 6 == cont[1]):
                                contributor = lms_db.execute("select name from contributors where id=?", (cont[0],)).fetchone()
                                if contributor is not None:
                                    track_artist=contributor[0]
                            elif album_artist is None and 5 == cont[1]:
                                contributor = lms_db.execute("select name from contributors where id=?", (cont[0],)).fetchone()
                                if contributor is not None:
                                    album_artist=contributor[0]
                        if album_artist is None:
                            album_artist = track_artist
                        elif track_artist is None:
                            track_artist = album_artist
                    if track_artist is not None and album_name is not None:
                        track_path='%s%s%s%s-%s.mp3' % (tmp_path, path[essentia_root_len:], CUE_TRACK, times[0], times[1])
                        tracks.append({'file':track_path, 'start':times[0], 'end':times[1], 'meta':{'title':row[1], 'artist':track_artist, 'albumartist':album_artist, 'album':album_name, 'genres':genre_list, 'duration':int(row[4])}})
    else:
        _LOGGER.debug("Can't get CUE tracks for %s - no LMS DB" % path)
    return tracks


def split_cue_track(path, track):
    _LOGGER.debug('Create %s' % track['file'])
    dirname=os.path.dirname(track['file'])
    end = float(track['end'])-float(track['start'])
    command=['ffmpeg', '-hide_banner', '-loglevel', 'panic', '-i', path, '-b:a', '128k', '-ss', track['start'], '-t', "%f" % end, track['file']]
    subprocess.Popen(command).wait()
    return True


def split_cue_tracks(files, num_threads):    
    # Create temporary folders
    for file in files:
        if 'track' in file:
            dirname=os.path.dirname(file['track']['file'])
            if not os.path.exists(dirname):
                os.makedirs(dirname)

    # Split into tracks
    futures_list = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for file in files:
            if 'track' in file:
                futures = executor.submit(split_cue_track, file['src'], file['track'])
                futures_list.append(futures)
        for future in futures_list:
            try:
                future.result()
            except Exception as e:
                _LOGGER.debug("Thread exception? - %s" % str(e))
                pass

                          
def convert_to_cue_url(path):
    cue = path.find(CUE_TRACK)
    if cue>0:
        parts = path.replace(CUE_TRACK, '#').split('#')
        path='file://'+quote(parts[0])+'#'+parts[1]
        return path[:-4]
    return path


def convert_from_cue_path(path):
    hsh = path.find('#')
    if hsh>0:
        return path.replace('#', CUE_TRACK)+'.mp3'
    return path


def convert_to_source(path):
    cue = path.find(CUE_TRACK)
    return path[:cue] if cue>0 else path
