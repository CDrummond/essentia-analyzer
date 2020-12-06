#!/usr/bin/env python3

import sqlite3
import sys

def normalize(s):
    if not s:
        return None
    return s.lower().replace('.', '').replace('(', '').replace(')', '').replace(' & ', ' and ')


def normalize_artist(artist):
    if not artist:
        return None
    return normalize(artist).replace(' feat ', ' ').replace(' ft ', ' ').replace(' featuring ', ' ')


conn = sqlite3.connect(sys.argv[1])
cursor = conn.cursor()

cursor.execute('SELECT file, artist, albumartist, album FROM tracks')
rows = cursor.fetchall()
for row in rows:
    cursor.execute('UPDATE tracks set artist=?, albumartist=?, album=? where file=?', (normalize_artist(row[1]), normalize_artist(row[2]), normalize(row[3]), row[0]))

conn.commit()
