#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, division

import os
import sys
import pwd
import json
from os import path
import logging
import argparse
import shlex
import shutil
import tempfile
import traceback
import subprocess

from .config import BIN_PATH, SYNC_USR, REPO_DIR, LOG_DIR, CFG_DIR, BIND_ADDR, EXTRA_DIR, RECORD_FILE, SYNC_METHODS

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
            pw = pwd.getpwnam(SYNC_USR)
        except KeyError:
            raise UserNotFound(SYNC_USR)
        self._uid = pw.pw_uid
        self._gid = pw.pw_gid

        self._extra = EXTRA_DIR
        if self._extra and not path.isdir(self._extra):
            raise NotADirectoryError(self._extra)

        self._record = RECORD_FILE
        self._methods = SYNC_METHODS

    def add(self, method, name, interval):

        repo = path.join(REPO_DIR, name)
        log = path.join(LOG_DIR, name)
        try_mkdir(repo)
        try_mkdir(log)

        self._methods[name] = method

        tab = subprocess.check_output(['crontab', '-l'])
        fd, p = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(tab)
                tmp.write('{} {} sync {name}\n'.format(interval, BIN_PATH, name=name).encode('utf-8'))
            subprocess.check_call(['crontab', '-e', p])
        except:
            traceback.print_exc()
        finally:
            os.remove(p)

    def sync(self, name, method=None):

        repo = path.join(REPO_DIR, name)
        if not path.isdir(repo):
            raise NotADirectoryError(repo)
        log = path.join(LOG_DIR, name)
        # Otherwise may be created by root
        try_mkdir(log)

        if method is None:
            m = self._methods.get(name)
            if not m:
                raise MissingSyncMethod(name)
            method = m

        if self._extra:
            args = 'docker run -i --rm -v {conf}:/opt/ustcsync/etc:ro -v {extra}:/usr/local/bin -v {repo}:/srv/repo/{name} -v {log}:/opt/ustcsync/log/{name} -e BIND_ADDRESS={bind_ip} -u {uid}:{gid} --name syncing-{name} --net=host ustclug/mirror:latest {method} {name}'.format(
                conf=CFG_DIR, extra=self._extra, repo=repo, log=log, bind_ip=BIND_ADDR, uid=self._uid, gid=self._gid, method=method, name=name)
        else:
            args = 'docker run -i --rm -v {conf}:/opt/ustcsync/etc:ro -v {repo}:/srv/repo/{name} -v {log}:/opt/ustcsync/log/{name} -e BIND_ADDRESS={bind_ip} -u {uid}:{gid} --name syncing-{name} --net=host ustclug/mirror:latest {method} {name}'.format(
                conf=CFG_DIR, repo=repo, log=log, bind_ip=BIND_ADDR, uid=self._uid, gid=self._gid, method=method, name=name)

        cmd = shlex.split(args)
        self._log.debug('Command: %s', cmd)
        retcode = subprocess.call(cmd)
        self._log.debug('Return: %s', retcode)

        if retcode == 0 and self._methods[name] != method:
            self._methods[name] = method

    def stop(self, name, timeout=60):

        args = 'docker stop -t {timeout} syncing-{name}'.format(
            timeout=timeout, name=name)
        cmd = shlex.split(args)
        self._log.debug('Command: %s', cmd)
        retcode = subprocess.call(cmd)
        self._log.debug('Return: %s', retcode)

    def list(self):
        for d in os.listdir(REPO_DIR):
            if not path.isdir(path.join(REPO_DIR, d)):
                self._log.warn('Not a directory: %s', d)
            else:
                print(d)

    def remove(self, name):

        try:
            shutil.rmtree(path.join(LOG_DIR, name))
        except:
            traceback.print_exc()

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        with open(RECORD_FILE, 'w') as fout:
            json.dump(self._methods, fout, indent=4)
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
        '-m',
        '--method',
        default='rsync',
        help='Sync method')
    add_pser.add_argument(
        '-i',
        '--interval',
        default='@hourly',
        help='Sync interval')
    add_pser.add_argument('name')

    sync_pser = subparsers.add_parser('sync',
                                      formatter_class=CustomFormatter,
                                      help='Start container to sync')
    sync_pser.add_argument(
        '-m',
        '--method',
        help='Sync method')
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

    rm_pser = subparsers.add_parser('remove', help='Remove repository')
    rm_pser.add_argument('name')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        parser.exit(1)

    args_dict = vars(args)
    # print(args_dict)
    get = args_dict.get

    with Manager(get('verbose')) as manager:
        if get('command') == 'add':
            manager.add(get('method'), get('name'), get('interval'))
        elif get('command') == 'sync':
            manager.sync(get('name'), get('method'))
        elif get('command') == 'stop':
            manager.stop(get('name'), get('timeout'))
        elif get('command') == 'list':
            manager.list()
        elif get('command') == 'remove':
            manager.remove(get('name'))

if __name__ == '__main__':
    main()
