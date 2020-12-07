#!/usr/bin/env python3

#
# Analyse files with essentia, and provide an API to retrieve similar tracks
#
# Copyright (c) 2020 Craig Drummond <craig.p.drummond@gmail.com>
# GPLv3 license.
#

import argparse
import logging
import os
from lib import analysis, config, tags, version

_LOGGER = logging.getLogger(__name__)
        
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Essentia analyzer (v%s)' % version.ESSENTIA_ANALYZER_VERSION)
    parser.add_argument('-c', '--config', type=str, help='Config file (default: config.json)', default='config.json')
    parser.add_argument('-l', '--log-level', action='store', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='INFO', help='Set log level (default: %(default)s)')
    parser.add_argument('-m', '--meta-only', action='store_true', default=False, help='Update metadata database only')
    parser.add_argument('-k', '--keep-old', action='store_true', default=False, help='Do not remove non-existant tracks from DB')
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=args.log_level, datefmt='%Y-%m-%d %H:%M:%S')
    cfg = config.read_config(args.config)
    analysis.analyse_files(cfg, not args.keep_old, args.meta_only)

