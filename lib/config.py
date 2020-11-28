#
# Analyse files with Essentia
#
# Copyright (c) 2020 Craig Drummond <craig.p.drummond@gmail.com>
# GPLv3 license.
#

import json
import logging
import os

_LOGGER = logging.getLogger(__name__)

def read_config(path):
    config={}

    if not os.path.exists(path):
        _LOGGER.error('%s does not exist' % path)
        exit(-1)
    try:
        with open(path, 'r') as configFile:
            config = json.load(configFile)
    except ValueError:
        _LOGGER.error('Failed to parse config file')
        exit(-1)
    except IOError:
        _LOGGER.error('Failed to read config file')
        exit(-1)

    for key in ['extractor']:
        if not key in config:
            _LOGGER.error("'%s' not in config file" % key)
            exit(-1)

    for key in ['essentia', 'lms']:
        if not key in config:
            _LOGGER.error("'%s' not in config file" % key)
            exit(-1)
        if not os.path.exists(config[key]):
            _LOGGER.error("'%s' does not exist" % config[key])
            exit(-1)

    for key in config:
        if key not in ['threads', 'extractor', 'port', 'genres', 'db', 'lmsdb', 'stop'] and not config[key].endswith('/'):
            config[key]=config[key]+'/'

    for path in ['tmp', 'json_cache']:
        if path in config and not os.path.exists(config[path]):
            _LOGGER.error("'%s' does not exist" % config[path])
            exit(-1)

    if not 'threads' in config:
        config['threads']=8

    return config
