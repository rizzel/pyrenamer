from pyrenamer.hasher import Hasher
from os.path import getsize


class QueueData:
    def __init__(self, file_name):
        self.file_name = file_name
        self.file_size = getsize(self.file_name)
        self.hasher = Hasher(self)
        """ :type: pyrenamer.hasher.Hasher """
        self.file_info = None
        """ :type: pyrenamer.file.FileInfo """
        self.anime_info = None
        """ :type: pyrenamer.anime.Anime """
