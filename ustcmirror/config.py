#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

__all__ = ['load_user_config']

import os
from os import path
import socket
import fcntl
import struct
import json


user_cfg_dir = path.join(path.expanduser('~'), '.ustcmirror')
if not path.isdir(user_cfg_dir):
    os.makedirs(user_cfg_dir)
user_cfg_path = path.join(user_cfg_dir, 'config.json')


def _get_ip(iface):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 0x8915: SIOCGIFADDR
    try:
        res = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack(
            '256s', iface[:15].encode('utf-8')))[20:24])
    except OSError as e:
        res = None
    return res


def load_user_config():
    cfg = {
        'REPO_DIR': '/srv/repo/',
        'LOG_DIR': '/opt/ustcsync/log/',
        'ETC_DIR': '/opt/ustcsync/etc/',
        'BIN_PATH': '/usr/local/bin/ustcmirror',
        'DB_PATH': path.join(user_cfg_dir, 'repos.db'),
        # The user who ran `ustcmirror`
        'SYNC_USR': 'mirror',
        # Only affect rsync/lftp/ftpsync
        'BIND_ADDR': 'eth0',
    }

    if path.isfile(user_cfg_path):
        with open(user_cfg_path, 'r') as fin:
            user_cfg = json.load(fin)
            for k in cfg.keys():
                if user_cfg.get(k):
                    cfg[k] = user_cfg.get(k)
        try:
            socket.inet_aton(cfg['BIND_ADDR'])
        except socket.error:
            # Possibly interface name
            cfg['BIND_ADDR'] = _get_ip(cfg['BIND_ADDR'])
    return cfg

if __name__ == '__main__':
    import pprint
    pprint.pprint(load_user_config())
