import logging
from sqlite3 import connect
from os.path import join, dirname

from pyrenamer import Singleton
import pyrenamer.config


class AniDB(metaclass=Singleton):
    def __init__(self):
        self.init_db()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(pyrenamer.config.debug_level.upper())

    @staticmethod
    def init_db():
        dbh = connect(pyrenamer.config.cache_db)
        with open(join(dirname(__file__), 'schema.sql')) as f:
            dbh.executescript(f.read())
