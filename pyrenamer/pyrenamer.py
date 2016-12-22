#!/usr/bin/env python3
from sqlite3 import connect
from argparse import ArgumentParser
from os.path import isdir, isfile, join, dirname
from os import walk
from queue import Queue

from pyrenamer.anidb import AniDBThread
from pyrenamer.hasher import HasherThread
import pyrenamer.config as config
from pyrenamer.queue_data import QueueData

ap = ArgumentParser(description="Detect anime, rename it and/or add it to anidb my list")
ap.add_argument('--mylist', '-m', action='store_true', help="Add the found files to my list")
ap.add_argument('--watched', '-w', action='store_true', help="If files are added to my list, mark them watched")
ap.add_argument('--rename', '-r', action='store_true', help="Rename the files according to rename.py")
ap.add_argument('files', nargs='+', help="List of files/folders to parse recursively")

hash_in = Queue()
hash_out = Queue()
anidb_out = Queue()

if __name__ == '__main__':
    args = ap.parse_args()

    if not args.mylist and not args.rename:
        ap.print_help()
        print("Please specify an action")
        exit(1)

    dbh = connect(config.cache_db)
    with open(join(dirname(__file__), 'schema.sql')) as f:
        dbh.executescript(f.read())

    file_list = []

    for f in args.files:
        if isdir(f):
            for path, dirs, files in walk(f):
                for ff in files:
                    complete = join(path, ff)
                    if isfile(complete):
                        file_list.append(QueueData(complete))

        elif isfile(f):
            file_list.append(QueueData(f))

    hasher = HasherThread(hash_in, hash_out)
    anidb = AniDBThread(hash_out, anidb_out)

    for f in file_list:
        hash_in.put(f)
    hash_in.put(None)

    while True:
        hash_item = anidb_out.get()
        """ :type: QueueData|None """
        if hash_item is None:
            break

        if args.rename:
            pass

        if args.mylist:
            if hash_item.file_info is not None:
                pass
            else:
                print("File {} could not be identified".format(hash_item.file_name))
