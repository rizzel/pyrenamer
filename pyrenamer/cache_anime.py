from sqlite3 import connect, Row

from pyrenamer.anime import Anime, AnimeRelated, AnimeTag
from pyrenamer.config import cache_db
from time import time
from datetime import datetime

from pyrenamer import row_hash


class CacheAnime:
    fields_str = ('year', 'type', 'url', 'picname',)
    fields_int = (
        'episodes_count', 'episode_max', 'episodes_special_count', 'rating', 'vote_count', 'rating_temp',
        'vote_count_temp', 'review_rating', 'review_count', 'ann_id', 'allcinema_id', 'animenfo_id',
        'specials_count', 'credits_count', 'other_count', 'trailer_count', 'parody_count', 'date_flags',
    )
    fields_date = ('date_air', 'date_end', 'record_updated',)
    fields_bool = ('is_restricted',)

    def __init__(self, aid, max_age=None):
        """

        :param int aid: The anime id
        :param int|None max_age: The maximum age of the cache entry
        """
        self.dbh = connect(cache_db)
        self.dbh.row_factory = Row

        self.aid = aid
        self._fields = []
        self._missing_fields = []

        self.anime = Anime(aid)

        c = self.dbh.cursor()
        c.execute('SELECT updated FROM anime WHERE aid = ?', (aid,))
        row = c.fetchone()
        if row is not None and max_age < time() - row[0]:
            self.delete()

    def read(self, fields):
        self._fields = fields
        self._missing_fields = fields[:]

        self._read_from_cache()
        if len(self._missing_fields):
            self._fetch_from_anidb()

        return self.anime

    def _read_from_cache(self):
        c = self.dbh.cursor()
        c.execute('SELECT * FROM anime WHERE aid = ?', (self.aid,))
        row = c.fetchone()
        if not row:
            return None

        row = row_hash(c, row)
        self.anime.updated = row['updated']

        for field in self._fields:
            if field in CacheAnime.fields_str:
                setattr(self.anime, field, row[field])
            elif field in CacheAnime.fields_int and row[field] is not None:
                setattr(self.anime, field, int(row[field]))
            elif field in CacheAnime.fields_bool and row[field] is not None:
                setattr(self.anime, field, bool(row[field]))
            elif field in CacheAnime.fields_date and row[field] is not None:
                setattr(self.anime, field, datetime.fromtimestamp(row[field]))
            if field in CacheAnime.fields_date or field in CacheAnime.fields_bool \
                    or field in CacheAnime.fields_int or field in CacheAnime.fields_str:
                self._missing_fields.remove(field)

        want_name = False
        for kind in ('romaji', 'kanji', 'english', 'other', 'short', 'synonym'):
            if 'name_'.format(kind) in self._fields:
                want_name = True
        if want_name:
            for kind in ('romaji', 'kanji', 'english'):
                if 'name_'.format(kind) in self._fields and row['has_name_{}'.format(kind)]:
                    setattr(self.anime.name, kind, '')
            for kind in ('other', 'short', 'synonym'):
                if 'name_'.format(kind) in self._fields and row['has_name_{}'.format(kind)]:
                    setattr(self.anime.name, kind, [])
            c.execute('SELECT `name`, name_type FROM anime_name WHERE aid = ?', (self.aid,))
            for row in c:
                if 'name_'.format(row[1]) in self._fields:
                    if row[1] in ('romaji', 'kanji', 'english'):
                        setattr(self.anime.name, kind, row[0])
                    else:
                        getattr(self.anime.name, kind).append(row[0])
                    self._missing_fields.remove('name_'.format(kind))

        if 'related' in self._fields:
            if row['has_related']:
                c.execute('SELECT related_aid, related_type FROM anime_related WHERE aid = ?', (self.anime.aid,))
                self.anime.related = {}
                for row in c:
                    self.anime.related.append(AnimeRelated(row[0], row[1]))
                self._missing_fields.remove('related')

        if 'award' in self._fields:
            if row['has_award']:
                c.execute('SELECT award FROM anime_award WHERE aid = ?', (self.anime.aid,))
                self.anime.award = []
                for row in c:
                    self.anime.award.append(row[0])
                self._missing_fields.remove('award')

        if 'tags' in self._fields:
            if row['has_tags']:
                self.anime.tags = {}
                c.execute('SELECT tag_id, tag_name, tag_weight FROM anime_tags WHERE aid = ?', (self.anime.aid,))
                for row in c:
                    self.anime.tags[row[0]] = AnimeTag(row[0], row[1], row[2])
                self._missing_fields.remove('tags')

        if 'characters' in self._fields:
            if row['has_characters']:
                self.anime.characters = []
                c.execute('SELECT cid FROM anime_character WHERE aid = ?', (self.anime.aid,))
                for row in c:
                    self.anime.characters.append(int(row[0]))
                self._missing_fields.remove('characters')

    def _fetch_from_anidb(self):
        pass

    def write_to_cache(self):
        c = self.dbh.cursor()
        c.execute('SELECT aid FROM anime WHERE aid = ?', (self.anime.aid,))
        row = c.fetchone()
        if not row:
            c.execute('INSERT INTO anime (aid) VALUES (?)', (self.anime.aid,))

        to_set = {}
        for key in CacheAnime.fields_bool + CacheAnime.fields_int + CacheAnime.fields_str:
            if getattr(self.anime, key) is not None:
                to_set[key] = getattr(self.anime, key)
        for key in CacheAnime.fields_date:
            if getattr(self.anime, key) is not None:
                to_set[key] = int(getattr(self.anime, key).timestamp())

        q = 'UPDATE anime SET {} WHERE aid = ?'.format(map(lambda k: '`{}` = ?', to_set.keys()))
        c.execute(q, list(to_set.values()) + [self.anime.aid])

        for l in ('romaji', 'kanji', 'english'):
            if getattr(self.anime.name, l) is not None:
                c.execute('DELETE FROM anime_name WHERE aid = ? AND name_type = ?', (self.anime.aid, l))
                c.execute("INSERT INTO anime_name (aid, name, name_type) VALUES (?, ?, ?)",
                          (self.anime.aid, getattr(self.anime.name, l), l))
                # noinspection SqlResolve
                c.execute('UPDATE anime SET has_name_{} = 1 WHERE aid = ?'.format(l), (self.anime.aid,))
        for l in ('other', 'short', 'synonym'):
            if getattr(self.anime.name, l) is not None:
                c.execute('DELETE FROM anime_name WHERE aid = ? AND name_type = ?', (self.anime.aid, l))
                for i in getattr(self.anime.name, l):
                    c.execute('INSERT INTO anime_name (aid, name, name_type) VALUES (?, ?, ?)', (self.anime.aid, i, l))
                    # noinspection SqlResolve
                    c.execute('UPDATE anime SET has_name_{} = 1 WHERE aid = ?'.format(l), (self.anime.aid,))

        if self.anime.award is not None:
            c.execute('DELETE FROM anime_award WHERE aid = ?', (self.anime.aid,))
            c.execute('INSERT INTO anime_award (aid, award) VALUES (?, ?)',
                      map(lambda a: (self.anime.aid, a), self.anime.award))
            c.execute('UPDATE anime SET has_award = 1 WHERE aid = ?', (self.anime.aid,))

        if self.anime.characters is not None:
            c.execute('DELETE FROM anime_character WHERE aid = ?', (self.anime.aid,))
            c.execute('INSERT INTO anime_character (aid, cid) VALUES (?, ?)',
                      map(lambda a: (self.anime.aid, a,), self.anime.characters))
            c.execute('UPDATE anime SET has_characters = 1 WHERE aid = ?', (self.anime.aid,))

        if self.anime.related is not None:
            c.execute('DELETE FROM anime_related WHERE aid = ?', (self.anime.aid,))
            for i in self.anime.related:
                c.execute('INSERT INTO anime_related (aid, related_aid, related_type) VALUES (?, ?, ?)',
                          (self.anime.aid, i.related_id, i.related_type))

        if self.anime.tags is not None:
            c.execute('DELETE FROM anime_tags WHERE aid = ?', (self.anime.aid,))
            for t in self.anime.tags:
                c.execute('INSERT INTO anime_tags (aid, tag_id, tag_name, tag_weight) VALUES (?, ?, ?, ?)',
                          (self.anime.aid, t.tag_id, t.tag_name, t.tag_weight))

    def delete(self):
        c = self.dbh.cursor()
        c.execute('DELETE FROM anime_tags WHERE aid = ?', (self.aid,))
        c.execute('DELETE FROM anime_related WHERE aid = ?', (self.aid,))
        c.execute('DELETE FROM anime_name WHERE aid = ?', (self.aid,))
        c.execute('DELETE FROM anime_character WHERE aid = ?', (self.aid,))
        c.execute('DELETE FROM anime_award WHERE aid = ?', (self.aid,))
        c.execute('DELETE FROM anime WHERE aid = ?', (self.aid,))
