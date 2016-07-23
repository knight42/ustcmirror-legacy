#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, absolute_import

import os
import sys
import pwd
import sqlite3
from os import path
import logging
import argparse
import shlex
import shutil
import tempfile
import traceback
import subprocess
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

from .config import load_user_config, user_cfg_path
_USER_CFG = load_user_config()
BIN_PATH = _USER_CFG['BIN_PATH']
SYNC_USR = _USER_CFG['SYNC_USR']
REPO_DIR = _USER_CFG['REPO_DIR']
LOG_DIR = _USER_CFG['LOG_DIR']
ETC_DIR = _USER_CFG['ETC_DIR']
BIND_ADDR = _USER_CFG['BIND_ADDR']
DB_PATH = _USER_CFG['DB_PATH']

from .utils import DbDict, docker_run


class CustomFormatter(argparse.HelpFormatter):

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                return ', '.join(action.option_strings)
            # if the Optional takes a value, format is:
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                option_string = ', '.join(action.option_strings)
            return '{} {}'.format(option_string, args_string)

    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help and action.default is not None:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += ' (default: %(default)s)'
        return help

if not __builtins__.get('NotADirectoryError'):
    class NotADirectoryError(Exception):
        pass


class UserNotFound(Exception):
    pass


class MissingSyncMethod(Exception):
    pass


def try_mkdir(d):
    if not path.isdir(d):
        if not path.exists(d):
            os.makedirs(d)
        else:
            raise NotADirectoryError(d)


class Manager(object):

    def __init__(self, verbose=False):

        if verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        self._log = logging.getLogger(__name__)
        self._log.setLevel(level)
        ch = logging.StreamHandler()
        fmter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s')
        ch.setFormatter(fmter)
        self._log.addHandler(ch)

        try:
            self._pw = pwd.getpwnam(SYNC_USR)
        except KeyError:
            raise UserNotFound(SYNC_USR)

        self._db = DbDict(self._init_db(DB_PATH))

    def add(self, name, prog, args, interval):

        repo = path.join(REPO_DIR, name)
        log = path.join(LOG_DIR, name.lower())
        try_mkdir(repo)
        try_mkdir(log)

        # Insert into db
        self._db[name] = (prog, args)

        tab = subprocess.check_output(['crontab', '-l'])
        fd, p = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(tab)
                tmp.write(
                    '{} {} sync {name}\n'.format(
                        interval,
                        BIN_PATH,
                        name=name).encode('utf-8'))
            subprocess.check_call(['crontab', p])
        except:
            self._log.warn('Error occurred:')
            traceback.print_exc()
        finally:
            os.remove(p)

    def sync(self, name):

        if not BIND_ADDR:
            raise ValueError('Invalid bind address')

        repo = path.join(REPO_DIR, name)
        if not path.isdir(repo):
            raise NotADirectoryError(repo)
        log = path.join(LOG_DIR, name.lower())
        # Otherwise may be created by root
        try_mkdir(log)

        if not self._db[name]:
            raise KeyError(name)
        prog, args = self._db[name]

        debug = self._log.level == logging.DEBUG

        if prog == 'ustcsync':
            ct = {
                'name': 'syncing-{}'.format(name),
                'rm': False if debug else True,
                'volumes': ['{}:/opt/ustcsync/etc:ro'.format(ETC_DIR), '{}:/opt/ustcsync/log/{}'.format(LOG_DIR, name.lower()), '{}:/srv/repo/{}'.format(repo, name)],
                'user': '{}:{}'.format(self._pw.pw_uid, self._pw.pw_gid),
                'image': 'ustclug/mirror:latest',
                'args': args,
                'env': 'BIND_ADDRESS={}'.format(BIND_ADDR),
                'net': 'host',
                'debug': debug
            }
            cmd = shlex.split(docker_run(**ct))
            self._log.debug('Command: %s', cmd)
        else:
            cmd = shlex.split('{} {}'.format(prog, args))

        if debug:
            subprocess.call(cmd)
        else:
            subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)

    def stop(self, name, timeout=60):

        args = 'docker stop -t {timeout} syncing-{name}'.format(
            timeout=timeout, name=name)
        cmd = shlex.split(args)
        self._log.debug('Command: %s', cmd)
        retcode = subprocess.call(cmd)
        self._log.debug('Docker return: %s', retcode)

    def list(self):

        for item in self._db:
            name, prog, args = item
            repo = path.join(REPO_DIR, name)
            if path.isdir(repo):
                print('Repository<{}>'.format(name), '{} {}'.format(prog, args))
            else:
                self._log.warn('Repository<%s> not exists', name)

    def remove(self, name):

        try:
            shutil.rmtree(path.join(LOG_DIR, name.lower()))
        except:
            traceback.print_exc()

        del self._db[name]

        tab = subprocess.check_output(['crontab', '-l']).decode('utf-8').splitlines()
        fd, p = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                for l in tab:
                    s = l.strip()
                    if s.startswith('#') or not s.endswith(name):
                        tmp.write(l + '\n')
            subprocess.check_call(['crontab', p])
        except:
            traceback.print_exc()
        finally:
            os.remove(p)

    def _init_db(self, f):

        conn = sqlite3.connect(f)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS repositories (
                          name TEXT primary key,
                          program TEXT,
                          args TEXT);""")
        cursor.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uniq_repo on repositories(name);""")
        conn.commit()
        return conn

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        self._db.close()
        return False


def main():

    parser = argparse.ArgumentParser(
        prog='ustcmirror',
        formatter_class=CustomFormatter)

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False)

    subparsers = parser.add_subparsers(
        help='Available commands', dest='command')

    add_pser = subparsers.add_parser('add',
                                     formatter_class=CustomFormatter,
                                     help='Add a new repository')
    add_pser.add_argument(
        '-p',
        '--program',
        default='ustcsync',
        help='Sync method')
    add_pser.add_argument(
        '-a',
        '--args',
        default='',
        help='Arguments passed to program')
    add_pser.add_argument(
        '-i',
        '--interval',
        default='@hourly',
        help='Sync interval')
    add_pser.add_argument('name')

    sync_pser = subparsers.add_parser('sync',
                                      formatter_class=CustomFormatter,
                                      help='Start container to sync')
    sync_pser.add_argument('name')

    stop_pser = subparsers.add_parser('stop',
                                      formatter_class=CustomFormatter,
                                      help='Stop container')
    stop_pser.add_argument(
        '-t',
        '--timeout',
        default='60')
    stop_pser.add_argument('name')

    subparsers.add_parser('list',
                          formatter_class=CustomFormatter,
                          help='List repositories')

    cfg_pser = subparsers.add_parser('config',
                                     formatter_class=CustomFormatter,
                                     help='')

    cfg_sub_pser = cfg_pser.add_subparsers(dest='config')
    cfg_set = cfg_sub_pser.add_parser(
        'set',
        formatter_class=CustomFormatter,
        help='Sets the config key to the value')
    cfg_set.add_argument('key')
    cfg_set.add_argument('value')
    cfg_get = cfg_sub_pser.add_parser(
        'get',
        formatter_class=CustomFormatter,
        help='Echo the config value to stdout')
    cfg_get.add_argument('key')
    cfg_sub_pser.add_parser('list', formatter_class=CustomFormatter,
                            help='Show all the config settings')

    rm_pser = subparsers.add_parser('remove', help='Remove repository')
    rm_pser.add_argument('name')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        parser.exit(0)

    args_dict = vars(args)
    get = args_dict.get

    if get('command') == 'config':
        if get('config') == 'get':
            print(_USER_CFG.get(get('key')))
        elif get('config') == 'list':
            for k, v in _USER_CFG.items():
                print(k, '=', v)
        elif get('config') == 'set':
            k = get('key')
            if k not in _USER_CFG:
                print('{} not exists!'.format(k))
                sys.exit(1)
            else:
                import json
                _USER_CFG[k] = get('value')
                with open(user_cfg_path, 'w') as out:
                    json.dump(_USER_CFG, out, indent=4)
        else:
            cfg_pser.print_help()
        sys.exit(0)

    with Manager(get('verbose')) as manager:
        if get('command') == 'add':
            if get('program') == 'ustcsync':
                if not get('args'):
                    args = get('name')
                else:
                    args = get('args')
            else:
                args = get('args') or ''
            manager.add(get('name'), get('program'), args, get('interval'))
        elif get('command') == 'sync':
            manager.sync(get('name'))
        elif get('command') == 'stop':
            manager.stop(get('name'), get('timeout'))
        elif get('command') == 'list':
            manager.list()
        elif get('command') == 'remove':
            manager.remove(get('name'))

if __name__ == '__main__':
    main()
