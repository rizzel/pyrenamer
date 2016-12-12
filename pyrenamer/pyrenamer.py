#!/usr/bin/env python3
from sqlite3 import connect
from argparse import ArgumentParser
from os.path import isdir, isfile, join, dirname
from os import walk
from queue import Queue

from pyrenamer.anidb import AniDBThread
from pyrenamer.hasher import HasherThread
import pyrenamer.config as config

ap = ArgumentParser(description="Detect anime, rename it and/or add it to anidb my list")
ap.add_argument('--mylist', '-m', action='store_true', help="Add the found files to my list")
ap.add_argument('--watched', '-w', action='store_true', help="If files are added to my list, mark them watched")
ap.add_argument('--rename', '-r', action='store_true', help="Rename the files according to rename.py")
ap.add_argument('files', nargs='+', help="List of files/folders to parse recursively")
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
                    file_list.append(complete)

    elif isfile(f):
        file_list.append(f)

hash_in = Queue()
hash_out = Queue()
hasher = HasherThread(hash_in, hash_out)

anidb_in = Queue()
anidb_out = Queue()
anidb = AniDBThread(anidb_in, anidb_out)

for f in file_list:
    hash_in.put(f)
hash_in.put(None)

while True:
    hash_item = hash_out.get()
    if hash_item is None:
        break

    if args.rename:

    if args.mylist:
