#!/usr/bin/python -O
# -*- coding: utf-8 -*-
__all__ = ['BIN_PATH', 'REPO_DIR', 'LOG_DIR', 'CFG_DIR', 'EXTRA_DIR', 'SYNC_USR', 'BIND_ADDR', 'RECORD_FILE', 'SYNC_METHODS']

REPO_DIR = '/srv/repo/'
LOG_DIR = '/opt/ustcsync/log/'
CFG_DIR = '/opt/ustcsync/etc/'
BIN_PATH = '/usr/local/bin/ustcmirror'

## Optional
EXTRA_DIR = ''

## The user who ran `ustcmirror`
SYNC_USR = 'mirror'

## Only affect rsync/lftp/ftpsync
BIND_ADDR = '202.141.176.110'

def _update_cfg(obj, *args):
    g = globals()
    cfg = {k: v for k, v in obj.items() if v}
    g.update(cfg)

import os
from os import path
import json
_user_cfg_dir = path.join(path.expanduser('~'), '.config', 'ustcmirror')
if not path.isdir(_user_cfg_dir):
    os.makedirs(_user_cfg_dir)
_user_cfg_path = path.join(_user_cfg_dir, 'config.json')
if path.isfile(_user_cfg_path):
    with open(_user_cfg_path, 'r') as cfg:
        _update_cfg(json.load(cfg), 'BIN_PATH', 'REPO_DIR', 'LOG_DIR', 'CFG_DIR', 'EXTRA_DIR', 'SYNC_USR', 'BIND_ADDR')

RECORD_FILE = path.join(_user_cfg_dir, 'sync_methods.json')
SYNC_METHODS = {}

if path.isfile(RECORD_FILE):
    with open(RECORD_FILE, 'r') as fin:
        SYNC_METHODS = json.load(fin)
else:
    ## Touch
    with open(RECORD_FILE, 'w') as fout:
        json.dump(SYNC_METHODS, fout)
