#!/usr/bin/env python3

#
# Analyse files with essentia, and provide an API to retrieve similar tracks
#
# Copyright (c) 2020-2021 Craig Drummond <craig.p.drummond@gmail.com>
# GPLv3 license.
#

import argparse
import os
import sqlite3
import sys
from lib import version


def info(s):
    print("INFO: %s" % s)


def error(s):
    print("ERROR: %s" % s)
    exit(-1)


def normalize_str(s):
    if not s:
        return s
    s=s.lower().replace('.', '').replace('(', '').replace(')', '').replace(' & ', ' and ')
    while '  ' in s:
        s=s.replace('  ', ' ')
    return s


def normalize_album(album):
    if not album:
        return album
    return normalize_str(album.replace(' (Anniversary Edition)', '') \
                              .replace(' (Deluxe Edition)', '') \
                              .replace(' (Expanded Edition)', '') \
                              .replace(' (Extended Edition)', '') \
                              .replace(' (Special Edition)', '') \
                              .replace(' (Deluxe)', '') \
                              .replace(' (Deluxe Version)', '') \
                              .replace(' (Extended Deluxe)', '') \
                              .replace(' (Super Deluxe)', '') \
                              .replace(' (Re-Issue)', '') \
                              .replace(' (Remastered)', '') \
                              .replace(' (Remixed)', '') \
                              .replace(' (Remixed And  Remastered)', ''))


def normalize_artist(artist):
    if not artist:
        return artist
    return normalize_str(artist).replace(' feat ', ' ').replace(' ft ', ' ').replace(' featuring ', ' ')


def ignore(conn, cursor, f):
    if not os.path.exists(f):
        error('%s does not exist' % f)

    try:
        lines=[]
        with open(f, 'r') as ifile:
            lines = ifile.readlines();
        cursor.execute('UPDATE tracks set ignore=0')
        for line in lines:
            val = line.strip()
            info('Ignore: %s' % val)
            cursor.execute('UPDATE tracks set ignore=1 where file like ?', ('{}%'.format(val),))
        conn.commit()
    except Exception as e:
        error('Failed to parse %s - %s' % (f, str(e)))


def normalize(conn, cursor):
    for t in ['artist', 'albumartist', 'album']:
        info('Normalizing: %s' % t)
        cursor.execute('SELECT DISTINCT %s FROM tracks' % t)
        rows = cursor.fetchall()
        for row in rows:
            if row[0] is not None:
                updated = normalize_album(row[0]) if 'album'==t else normalize_artist(row[0])
            if row[0]!=updated:
                cursor.execute('UPDATE tracks set %s=? where %s=?' % (t, t), (updated, row[0]))
    conn.commit()

    #cursor.execute('SELECT file, artist, albumartist, album FROM tracks')
    #rows = cursor.fetchall()
    #tags.normalizeTags=True
    #for row in rows:
    #    cursor.execute('UPDATE tracks set artist=?, albumartist=?, album=? where file=?', (tags.normalize_artist(row[1]), tags.normalize_artist(row[2]), tags.normalize_album(row[3]), row[0]))
    #conn.commit()


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Update Essentia DB (v%s)' % version.ESSENTIA_ANALYZER_VERSION)
    parser.add_argument('-d', '--db', type=str, help='Database file', default='essentia.db')
    parser.add_argument('-i', '--ignore', type=str, help='Path to file containing items to ignore', default=None)
    parser.add_argument('-n', '--normalize', dest='normalize', action='store_true', help='Normalize artist, albumartist, and album', default=False)
    args = parser.parse_args()

    if not args.normalize and args.ignore is None:
        info("Nothing todo")
    else:
        try:
            conn = sqlite3.connect(args.db)
            cursor = conn.cursor()
        except:
            error("Failed to open DB")

        if args.ignore is not None:
            ignore(conn, cursor, args.ignore)

        if args.normalize:
            normalize(conn, cursor)

