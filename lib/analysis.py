#
# Analyse files with Essentia
#
# Copyright (c) 2020 Craig Drummond <craig.p.drummond@gmail.com>
# GPLv3 license.
#

import json
import logging
import os
import sqlite3
import subprocess
import tempfile
from . import cue, tracks_db, tags
from concurrent.futures import ThreadPoolExecutor

_LOGGER = logging.getLogger(__name__)
AUDIO_EXTENSIONS = ['m4a', 'mp3', 'ogg', 'flac']

def get_files_to_analyse(db, lms_db, lms_path, path, files, essentia_root_len, tmp_path, tmp_path_len, meta_only):
    if not os.path.exists(path):
        _LOGGER.error("'%s' does not exist" % path)
        return
    if os.path.isdir(path):
        for e in sorted(os.listdir(path)):
            get_files_to_analyse(db, lms_db, lms_path, os.path.join(path, e), files, essentia_root_len, tmp_path, tmp_path_len, meta_only)
    elif path.rsplit('.', 1)[1].lower() in AUDIO_EXTENSIONS:
        if os.path.exists(path.rsplit('.', 1)[0]+'.cue'):
            for track in cue.get_cue_tracks(lms_db, lms_path, path, essentia_root_len, tmp_path):
                if meta_only or not db.file_already_analysed(track['file'][tmp_path_len:]):
                    files.append({'abs':track['file'], 'db':track['file'][tmp_path_len:], 'track':track, 'src':path})
        elif meta_only or not db.file_already_analysed(path[essentia_root_len:]):
            files.append({'abs':path, 'db':path[essentia_root_len:]})

    
def analyze_track(idx, db_path, abs_path, tmp_path, config, total):
    if 'stop' in config and os.path.exists(config['stop']):
        return None
    _LOGGER.debug("[%d/%d] Analyze: %s" % (idx, total, db_path))
    if 'json_cache' in config:
        jsfile = "%s/%s.json" % (config['json_cache'], db_path)
        path = jsfile[:-(len(os.path.basename(jsfile)))-1]
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                pass
    else:
        jsfile = "%s/essentia-%d.json" % (tmp_path, idx)
    if not os.path.exists(jsfile):
        subprocess.call([config['extractor'], abs_path, jsfile, "profile"], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(jsfile):
        return None
    try:
        resp = None
        with open(jsfile, 'r') as js:
            data = json.load(js)
            resp = {
                      'path': db_path,
                      'tags': tags.read_tags(abs_path, tracks_db.GENRE_SEPARATOR),
                      'danceable': float(data['highlevel']['danceability']['all']['danceable']),
                      'aggressive': float(data['highlevel']['mood_aggressive']['all']['aggressive']),
                      'electronic': float(data['highlevel']['mood_electronic']['all']['electronic']),
                      'acoustic': float(data['highlevel']['mood_acoustic']['all']['acoustic']),
                      'happy': float(data['highlevel']['mood_happy']['all']['happy']),
                      'party': float(data['highlevel']['mood_party']['all']['party']),
                      'relaxed': float(data['highlevel']['mood_relaxed']['all']['relaxed']),
                      'sad': float(data['highlevel']['mood_sad']['all']['sad']),
                      'dark': float(data['highlevel']['timbre']['all']['dark']),
                      'tonal': float(data['highlevel']['tonal_atonal']['all']['tonal']),
                      'voice': float(data['highlevel']['voice_instrumental']['all']['voice']),
                      'bpm': int(data['rhythm']['bpm'])
                    }
        if not 'json_cache' in config:
            os.remove(jsfile)
        return resp
    except ValueError:
        _LOGGER.error('Failed to parse %s for %s' % (jsfile, db_path))
    return None


def analyze_tracks(db, allfiles, tmp_path, config, total):
    numtracks = len(allfiles)
    futures_list = []
    count_since_save = 0
    with ThreadPoolExecutor(max_workers=config['threads']) as executor:
        for i in range(numtracks):
            futures = executor.submit(analyze_track, i, allfiles[i]['db'], allfiles[i]['abs'], tmp_path, config, total)
            futures_list.append(futures)
        for future in futures_list:
            try:
                result = future.result()
                if result:
                    count_since_save += 1
                    db.add(result)
                    if count_since_save >= 750:
                        _LOGGER.debug('Commiting DB changes')
                        db.commit()
                        count_since_save = 0
            except Exception as e:
                _LOGGER.debug("Thread exception? - %s" % str(e))
                pass

def analyse_files(config, remove_tracks, meta_only): # TODO meta_only
    _LOGGER.debug('Music path: %s' % config['essentia'])
    db = tracks_db.TracksDb(config)
    lms_db = sqlite3.connect(config['lmsdb']) if 'lmsdb' in config else None
    temp_dir = config['tmp'] if 'tmp' in config else None
    removed_tracks = db.remove_old_tracks(config['essentia']) if remove_tracks and not meta_only else False

    with tempfile.TemporaryDirectory(dir=temp_dir) as tmp_path:
        _LOGGER.debug('Temp folder: %s' % tmp_path)
        files=[]
        get_files_to_analyse(db, lms_db, config['lms'], config['essentia'], files, len(config['essentia']), tmp_path+'/', len(tmp_path)+1, meta_only)
        _LOGGER.debug('Num tracks to update: %d' % len(files))
        cue.split_cue_tracks(files, config['threads'])
        num_to_analyze = len(files)
        if num_to_analyze>0 or removed_tracks:
            if num_to_analyze>0 and not meta_only:
                analyze_tracks(db, files, tmp_path, config, num_to_analyze)
            db.commit()
            db.close()
    _LOGGER.debug('Finished analysis')
