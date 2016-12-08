import logging

from pyrenamer import Singleton
import pyrenamer.config


class AniDB(metaclass=Singleton):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(pyrenamer.config.debug_level.upper())

