#!/usr/bin/env python3

anidb_client_name = 'pyrenamer'
anidb_client_version = 1
anidb_api_version = 3


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def row_hash(cursor, row):
    if row is None:
        return None
    ret = {}
    for i in range(len(row)):
        ret[cursor.description[i][0]] = row[i]
    return ret
