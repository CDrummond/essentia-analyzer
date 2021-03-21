#
# Analyse files with Essentia
#
# Copyright (c) 2020-2021 Craig Drummond <craig.p.drummond@gmail.com>
# GPLv3 license.
#

import json
import logging
import os
import sqlite3
from . import cue, tags

GENRE_SEPARATOR = ';'
_LOGGER = logging.getLogger(__name__)

class TracksDb(object):
    def __init__(self, config):
        _LOGGER.debug('DB: %s' % config['db'])
        self.conn = sqlite3.connect(config['db'])
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tracks (
                    file varchar PRIMARY KEY NOT NULL,
                    title varchar,
                    artist varchar,
                    album varchar,
                    albumartist varchar,
                    genre varchar,
                    duration integer,
                    ignore integer,
                    danceable integer,
                    aggressive integer,
                    electronic integer,
                    acoustic integer,
                    happy integer,
                    party integer,
                    relaxed integer,
                    sad integer,
                    dark integer,
                    tonal integer,
                    voice integer,
                    bpm integer)''')
        self.cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS tracks_idx ON tracks(file)')
        # Add 'title' column - will fail if already exists (which it should, but older instances might not have it)
        try:
            self.cursor.execute('ALTER TABLE tracks ADD COLUMN title varchar default null')
        except:
            pass


    def commit(self):
        self.conn.commit()


    def close(self):
        self.cursor.close()
        self.conn.close()


    def add(self, track):
        genre = None
        if 'genres' in track['tags'] and track['tags']['genres'] is not None:
            genre = GENRE_SEPARATOR.join(track['tags']['genres'])

        albumartist = None
        if 'albumartist' in track['tags'] and track['tags']['albumartist'] is not None:
            albumartist = track['tags']['albumartist']

        self.cursor.execute('INSERT INTO tracks (file, title, artist, album, albumartist, genre, duration, ignore, danceable, aggressive, electronic, acoustic, happy, party, relaxed, sad, dark, tonal, voice, bpm) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (track['path'], track['tags']['title'], track['tags']['artist'], track['tags']['album'], albumartist, genre, track['tags']['duration'], 0, track['danceable'], track['aggressive'], track['electronic'], track['acoustic'], track['happy'], track['party'], track['relaxed'], track['sad'], track['dark'], track['tonal'], track['voice'], track['bpm']))


    def update(self, track):
        genre = None
        if 'genres' in track['tags'] and track['tags']['genres'] is not None:
            genre = GENRE_SEPARATOR.join(track['tags']['genres'])

        albumartist = None
        if 'albumartist' in track['tags'] and track['tags']['albumartist'] is not None:
            albumartist = track['tags']['albumartist']

        self.cursor.execute('UPDATE tracks SET title=?, artist=?, album=?, albumartist=?, genre=?, duration=? WHERE file=?', (track['tags']['title'], track['tags']['artist'], track['tags']['album'], albumartist, genre, track['tags']['duration'], track['path']))


    def remove_old_tracks(self, source_path):
        non_existant_files = []
        _LOGGER.debug('Looking for old tracks to remove')
        try:
            self.cursor.execute('SELECT file FROM tracks')
            rows = self.cursor.fetchall()
            for row in rows:
                if not os.path.exists(os.path.join(source_path, cue.convert_to_source(row[0]))):
                    _LOGGER.debug("'%s' no longer exists" % row[0])
                    non_existant_files.append(row[0])

            _LOGGER.debug('Num old tracks: %d' % len(non_existant_files))
            if len(non_existant_files)>0:
                # Remove entries...
                for path in non_existant_files:
                    self.cursor.execute('DELETE from tracks where file=?', (path, ))
                return True
        except Exception as e:
            _LOGGER.error('Failed to remove old tracks - %s' % str(e))
            pass
        return False


    def file_already_analysed(self, path):
        self.cursor.execute('SELECT danceable FROM tracks WHERE file=?', (path,))
        return self.cursor.fetchone() is not None


    def get_cursor(self):
        return self.cursor
