import hashlib
from os.path import isfile, getsize
from threading import Thread
from queue import Queue
from time import time
from sys import stderr


class Hasher:
    def __init__(self, file_name):
        self.file_name = file_name
        if not isfile(self.file_name):
            raise Exception("File {} does not exist!".format(file_name))
        self.progress_queue = Queue(5)
        self.last_time = 0
        self.progress = HasherProgress(self.progress_queue)

    def hash(self):
        h = hashlib.new('md4')
        self.progress.start()
        size = getsize(self.file_name)
        read = 0
        with open(self.file_name, 'rb') as f:
            while True:
                data = f.read(4 * 1024 * 1024)
                if len(data) == 0:
                    break
                read += len(data)
                if self.last_time < time() - 1:
                    self.progress_queue.put(100 * read / size)
                h.update(data)
        return h


class HasherProgress(Thread):
    def __init__(self, progress_queue):
        super().__init__()
        self.progress_queue = progress_queue
        """ :type: Queue """

    def run(self):
        while True:
            progress = self.progress_queue.get()
            if progress is None:
                break
            print("\e[1;37m\b\b\b\b\b {: 3d}%\e[m".format(progress), end='', file=stderr, flush=True)
