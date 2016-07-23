#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, generators
__all__ = ['DbDict', 'docker_run']

import traceback


class DbDict(object):

    # Not thread-safe
    _cache = {}

    def __init__(self, conn, table='repositories'):

        self._table = table
        self._conn = conn
        self._cursor = conn.cursor()

    def __getitem__(self, name):

        v = DbDict._cache.get(name)
        if v:
            return v
        sql = 'SELECT program, args FROM {} WHERE name = ?;'.format(self._table)
        try:
            self._cursor.execute(sql, (name,))
            DbDict._cache[name] = self._cursor.fetchone()
        except:
            traceback.print_exc()
            DbDict._cache[name] = None
        return DbDict._cache[name]

    def __setitem__(self, name, v):

        sql = 'INSERT INTO {} (name, program, args) VALUES (?, ?, ?);'.format(self._table)
        self._cursor.execute(sql, (name, v[0], v[1]))
        self._conn.commit()
        DbDict._cache[name] = v

    def __delitem__(self, name):

        self._cursor.execute('DELETE FROM {} WHERE name = ?;'.format(self._table), (name,))
        self._conn.commit()
        if DbDict._cache.get(name):
            del DbDict._cache[name]

    def __iter__(self):

        sql = 'SELECT name, program, args FROM {};'.format(self._table)
        try:
            self._cursor.execute(sql)
            for item in self._cursor:
                yield item
        except:
            traceback.print_exc()

    def keys(self):

        for item in self:
            yield item[0]

    def values(self):

        for item in self:
            yield item[1:]

    def items(self):

        for item in self:
            yield (item[0], item[1:])

    def close(self):

        self._conn.close()


def docker_run(image, args, debug=False, rm=False,
               detach=False, volumes=None, **kwargs):
    cmd = 'docker run'
    if debug:
        cmd += ' -e DEBUG=true'
    if rm and detach:
        raise ValueError('Cannot specify --rm and -d at the same time')
    if rm:
        cmd += ' --rm'
    if detach:
        cmd += ' --d'
    if volumes:
        if not isinstance(volumes, list):
            volumes = [volumes]
        cmd += ' ' + ' '.join(map(lambda x: '-v {}'.format(x), volumes))
    for k, v in kwargs.items():
        if v is None:
            cmd += ' --{}'.format(k)
        else:
            cmd += ' --{} {}'.format(k, v)
    cmd += ' {} {}'.format(image, args)
    return cmd

if __name__ == '__main__':
    pass
