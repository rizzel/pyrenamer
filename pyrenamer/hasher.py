import hashlib
from os.path import isfile, getsize
from threading import Thread
from time import time
from sys import stderr


class Hasher:
    def __init__(self, queue_data):
        """

        :param pyrenamer.queue_data.QueueData queue_data: The file to hash
        """
        self._queue_data = queue_data
        if not isfile(self._queue_data.file_name):
            raise Exception("File {} does not exist!".format(self._queue_data.file_name))
        self._last_time = 0
        self.hash = None

    def calc_hash(self):
        self.hash = hashlib.new('md4')
        size = self._queue_data.file_size
        read = 0
        with open(self._queue_data.file_name, 'rb') as f:
            while True:
                data = f.read(4 * 1024 * 1024)
                if len(data) == 0:
                    break
                read += len(data)
                if self._last_time < time() - 1:
                    print("\e[1;37m\b\b\b\b\b {: 3d}%\e[m".format(100 * read / size), end='', file=stderr, flush=True)
                self.hash.update(data)


class HasherThread(Thread):
    def __init__(self, in_queue, out_queue):
        """

        :param queue.Queue in_queue: The incoming queue
        :param queue.Queue out_queue: The outgoing queue
        """
        super().__init__()
        self._in_queue = in_queue
        self._out_queue = out_queue

    def run(self):
        while True:
            item = self._in_queue.get()
            """ :type: pyrenamer.queue_data.QueueData|None """
            if item is None:
                self._out_queue.put(None)
                return
            item.hasher.calc_hash()
            self._out_queue.put(item)
