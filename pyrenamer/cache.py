from sqlite3 import connect
from pyrenamer.config import cache_db
from time import time


class Cache:
    def __init__(self):
        self.dbh = connect(cache_db)

    def get(self, key, max_age=None):
        """
        Get a key from cache

        :param str key: the key to fetch
        :param int|None max_age: the max age in seconds or None if not used
        """
        c = self.dbh.cursor()
        if max_age is None:
            c.execute('SELECT value FROM cache WHERE `key` = ?', (key,))
        else:
            c.execute('SELECT value FROM cache WHERE `key` = ? AND created > ?', (key, time() - max_age))
        if c:
            row = c.fetchone()
            return row[0]
        return None

    def set(self, key, value):
        """
        Set a key in the cache

        :param str key: The key
        :param mixed value: The value
        """
        self.dbh.execute('INSERT INTO cache (`key`, value, created) VALUES (?, ?, ?)', (key, value, time()))
