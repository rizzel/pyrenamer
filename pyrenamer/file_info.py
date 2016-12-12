class FileInfo:
    def __init__(self, queue_data, anidb_queue_in, anidb_queue_out):
        """

        :param pyrenamer.queue_data.QueueData queue_data:
        :param queue.Queue anidb_queue_in:
        :param queue.Queue anidb_queue_out:
        """
        self._queue_data = queue_data
        self._anidb_queue_in = anidb_queue_in
        self._anidb_queue_out = anidb_queue_out
        self.fid = None
        """ :type: int """

    def get_fid(self):
        self._anidb_queue_in.put((
            'FILE',
            self._queue_data.hasher.hash.hex_digest(),
            self._queue_data.file_size,
            r'0000000000',
            r'00000000'
        ))
        self.fid = int(list(self._anidb_queue_out.get())[0])

    def get_info(self):


