# Essentia Analyzer

Simple python3 script to analyze music files with Essentia and store details in
an SQLite database. This DB can then be used by [Essentia API Server](https://github.com/CDrummond/essentia-api)
to provide a HTTP API to retrieve similar tracks. This API is in turn used by the
[LMS Similarity Plugin](https://github.com/CDrummond/lms-musicsimilarity) to
provide a 'Dont Stop The Music' mixer.


## Analysing Tracks

```
./essentia-analyzer.py -c config.json -l DEBUG
```

### CUE files

If the analysis locates a music file with a similarly named CUE file (e.g.
`artist/album/album name.flac` and `artist/album/album name.cue`) then it will
read the track listing from the LMS db file and use `ffmpeg` to split the
music file into temporary 128kbps MP3 files for analysis. The files are removed
once analysis is complete.


## Configuration

The script reads its configuration from a JSON file (default name is `config.json`).
This has the following format:

```
{
 "extractor":"bin/x86-64/essentia_streaming_extractor_music",
 "essentia":"/home/Music/",
 "lms":"/media/Music/",
 "tmp":"/tmp/",
 "db":"/home/user/.local/share/essentia.db",
 "lmsdb":"/path/to/lms/Cache/library.db",
 "json_cache":"/path/to/store/essentia/json/files/",
 "stop":"stop",
 "threads":7,
 "normalize":false
}
```

* `extractor` contains the location of the Essentia extractor binary.
* `essentia` is the path to your music files on the current machine. This script
will store music paths relative to the path configured here. e.g. if this is set
to `/home/user/Music/` then `/home/user/Music/ABBA/Greatest Hits/Waterloo.mp3` will
be stored as `ABBA/Greatest Hits/Waterloo.mp3`
* `lms` is the path of your music as LMS sees it. This is needed when analyzing
CUE files. The script will look for track details in LMS's db and use this config
item to ammend the paths as required. e.g. if `lms` is set to `/disk2/Music` and
`essentia` set to `/home/user/Music/` the script will convert `/disk2/Music/Artist/Album.cue`
to `/home/user/Music/Artist/Album.cue` This is to cater for cases where LMS is on
another machine (e.g. a raspberry pi) but you want to analyze on a faster machine.
* `tmp` when handling CUE files, the script will use this directory to store the
temporary MP3 files.
* `db` is the name of the database file that will be created.
* `lmsdb` should contain the location of LMS's library DB. This is only required
if handling CUE files.
* `json_cache` The Essentia music extractor outputs JSON files containing the
analyzed information. By default these JSON files are written to the `tmp`
directory and removed when done. To keep these files, for later usage, you can
specify an alternative folder via `json_cache` - and these files will not be
removed.
* `stop` when runnnig the script will check for the presence of the filename set
here, and if found the script will gracefully terminate. This allows you to start
analyzing a large music collection but stop half way through. (When re-started
the anlyzer will resume from where it stopped).
* `threads` Number of threads to use during analysis phase. This controls how
many calls to `ffmpeg` are made concurrently, and how many concurrent tracks
essentia is asked to analyse.

## Normalizing artists, albums, etc.

To 'normalize' certain strings (e.g. remove brackets, convert to lowercase, etc)
use the `update-db.py` script: e.g.

```
./update-db.py --db essentia.db --normalize
```

**NOTE** This normalzing will change the DB entries, so its better to take a copy
of the non-normalized database so that you can revert changes. In future I might
remove this option here and do the normalization in `essentia-api` when it reads
info from the database.

## Ignoring artists, albums, etc.

To mark certains items as 'ignored' (i.e. so that they are not added to mixes),
create a text file where each line contains the unique path, e.g.:

```
AC-DC/Power Up/
The Police/
```

Then call:

```
./update-db.py --db essentia.db --ignore ignore.txt
```

This basically sets the `ignore` column to 1 for all items whose file starts
with one of the listed lines.

Setting a track's `ignore` to `1` will cause the API to not use this track if
it is returned as a similar track by essentia. In this way you can exclude
specific tracks from being added to mixes - but if they are already in the
queue, then they can sill be used as seed tracks.

## Credits

The Essentia binary is taken from Roland0's  [LMS Essentia Integration](https://www.nexus0.net/pub/sw/lmsessentia/)
