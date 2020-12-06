#
# Analyse files with Essentia
#
# Copyright (c) 2020 Craig Drummond <craig.p.drummond@gmail.com>
# GPLv3 license.
#

import json
import logging

_LOGGER = logging.getLogger(__name__)

normalizeTags = False

def get_ogg_or_flac(path):
    from mutagen.oggflac import OggFLAC
    from mutagen.oggopus import OggOpus
    from mutagen.oggvorbis import OggVorbis
    from mutagen.flac import FLAC

    try:
        return OggVorbis(path)
    except:
        pass
    try:
        return FLAC(path)
    except:
        pass
    try:
        return OggFLAC(path)
    except:
        pass
    try:
        return OggOpus(path)
    except:
        pass
    return None


def normalize(s):
    global normalizeTags
    if not normalizeTags or not s:
        return s
    return s.lower().replace('.', '').replace('(', '').replace(')', '').replace(' & ', ' and ')


def normalize_artist(artist):
    global normalizeTags
    if not normalizeTags or not artist:
        return artist
    return normalize(artist).replace(' feat ', ' ').replace(' ft ', ' ').replace(' featuring ', ' ')


def read_tags(path, genre_separator):
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4

    try:
        audio = MP4(path)
        tags = {'artist':normalize_artist(str(audio['\xa9ART'][0])), 'album':normalize(str(audio['\xa9alb'][0])), 'duration':int(audio.info.length), 'albumartist':None, 'genres':None}
        if 'aART' in audio:
            tags['albumartist']=normalize_artist(str(audio['aART'][0]))
        if '\xa9gen' in audio:
            tags['genres']=[]
            for g in audio['\xa9gen']:
                tags['genres'].append(str(g))
        #_LOGGER.debug('MP4 File: %s Meta: %s' % (path, json.dumps(tags)))
        return normalize_tags(tags)
    except:
        pass

    try:
        audio = MP3(path)
        tags = {'artist':normalize_artist(str(audio['TPE1'])), 'album':normalize(str(audio['TALB'])), 'duration':int(audio.info.length), 'albumartist':None, 'genres':None}
        if 'TPE2' in audio:
            tags['albumartist']=normalize_artist(str(audio['TPE2']))
        if 'TCON' in audio:
            tags['genres']=str(audio['TCON']).split(genre_separator)
        #_LOGGER.debug('MP3 File: %s Meta: %s' % (path, json.dumps(tags)))
        return normalize_tags(tags)
    except Exception as e:
        #print("EX:%s" % str(e))
        pass

    try:
        audio = ID3(path)
        tags = {'artist':normalize_artist(str(audio['TPE1'])), 'album':normalize(str(audio['TALB'])), 'duration':0, 'albumartist':None, 'genres':None}
        if 'TPE2' in audio:
            tags['albumartist']=normalize_artist(str(audio['TPE2']))
        if 'TCON' in audio:
            tags['genres']=str(audio['TCON']).split(genre_separator)
        #_LOGGER.debug('ID3 File: %s Meta: %s' % (path, json.dumps(tags)))
        return normalize_tags(tags)
    except:
        pass

    audio = get_ogg_or_flac(path)
    if audio:
        tags = {'artist':normalize_artist(str(audio['ARTIST'][0])), 'album':normalize(str(audio['ALBUM'][0])), 'duration':int(audio.info.length), 'albumartist':None, 'genres':None}
        if 'ALBUMARTIST' in audio:
            tags['albumartist']=normalize_artist(str(audio['ALBUMARTIST'][0]))
        if 'GENRE' in audio:
            tags['genres']=[]
            for g in audio['GENRE']:
                tags['genres'].append(str(g))
        #_LOGGER.debug('OGG File: %s Meta: %s' % (path, json.dumps(tags)))
        return normalize_tags(tags)

    _LOGGER.debug('File:%s Meta:NONE' % path)
    return None
