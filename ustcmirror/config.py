#!/usr/bin/python -O
# -*- coding: utf-8 -*-

REPO_DIR = '/srv/repo/'
LOG_DIR = '/opt/ustcsync/log/'
CFG_DIR = '/opt/ustcsync/etc/'

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

import json
from os import path
_user_cfg_path = path.join(path.expanduser('~'), '.ustcmirror.json')
if path.isfile(_user_cfg_path):
    with open(_user_cfg_path, 'r') as cfg:
        _update_cfg(json.load(cfg), 'REPO_DIR', 'LOG_DIR', 'CFG_DIR', 'EXTRA_DIR', 'SYNC_USR', 'BIND_ADDR')
