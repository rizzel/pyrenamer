from sqlite3 import connect

from pyrenamer.anime import AnimeRelated, AnimeTag
from pyrenamer.config import cache_db
from datetime import datetime

from pyrenamer import row_hash
from pyrenamer.rename import anime_info_fields
from pyrenamer.config import anidb_update_interval


class AnimeCache:
    fields_str = ('year', 'type', 'url', 'picname',)
    fields_int = (
        'episodes_count', 'episode_max', 'episodes_special_count', 'rating', 'vote_count', 'rating_temp',
        'vote_count_temp', 'review_rating', 'review_count', 'ann_id', 'allcinema_id', 'animenfo_id',
        'specials_count', 'credits_count', 'other_count', 'trailer_count', 'parody_count', 'date_flags',
        'name_english', 'name_kanji', 'name_romaji',
    )
    fields_date = ('date_air', 'date_end', 'record_updated',)
    fields_bool = ('is_restricted',)

    def __init__(self, anime):
        """

        :param pyrenamer.anime.Anime anime: The anime to fill
        """
        self.dbh = connect(cache_db)

        self._was_read = False

        self.anime = anime
        self._missing_fields = []
        for k, v in anime_info_fields:
            if v:
                self._missing_fields.append(k)

        c = self.dbh.cursor()
        c.execute('SELECT updated FROM anime WHERE aid = ?', (self.anime.aid,))
        row = c.fetchone()
        if row is not None:
            updated = datetime.fromtimestamp(row[0])
            if datetime.now() - anidb_update_interval < updated:
                self.delete()

    def read(self):
        if not self._was_read:
            self._was_read = True
            self._read_from_cache()
            if len(self._missing_fields):
                self._read_from_anidb()
                self._write_to_cache()

    def _read_from_cache(self):
        c = self.dbh.cursor()
        c.execute('SELECT * FROM anime WHERE aid = ?', (self.anime.aid,))
        row = c.fetchone()
        if not row:
            return None

        row = row_hash(c, row)
        self.anime.updated = datetime.fromtimestamp(row['updated'])

        for field in self._missing_fields:
            if field in AnimeCache.fields_str:
                setattr(self.anime, field, row[field])
            elif field in AnimeCache.fields_int and row[field] is not None:
                setattr(self.anime, field, int(row[field]))
            elif field in AnimeCache.fields_bool and row[field] is not None:
                setattr(self.anime, field, bool(row[field]))
            elif field in AnimeCache.fields_date and row[field] is not None:
                setattr(self.anime, field, datetime.fromtimestamp(row[field]))
            if field in AnimeCache.fields_date or field in AnimeCache.fields_bool \
                    or field in AnimeCache.fields_int or field in AnimeCache.fields_str:
                self._missing_fields.remove(field)

        for kind in ('other', 'short', 'synonym'):
            if 'name_{}'.format(kind) in self._missing_fields and row['has_name_{}'.format(kind)]:
                setattr(self.anime, 'name_{}'.format(kind), [])
                c.execute('SELECT `name` FROM anime_names WHERE aid = ? AND name_type = ?', (self.anime.aid, kind))
                for row in c:
                    getattr(self.anime, 'name_{}'.format(kind)).append(row[0])
                self._missing_fields.remove('name_{}'.format(kind))

        if 'related' in self._missing_fields:
            if row['has_related']:
                c.execute('SELECT related_aid, related_type FROM anime_related WHERE aid = ?', (self.anime.aid,))
                self.anime.related = {}
                for row in c:
                    self.anime.related.append(AnimeRelated(row[0], row[1]))
                self._missing_fields.remove('related')

        if 'awards' in self._missing_fields:
            if row['has_awards']:
                c.execute('SELECT award FROM anime_awards WHERE aid = ?', (self.anime.aid,))
                self.anime.award = []
                for row in c:
                    self.anime.award.append(row[0])
                self._missing_fields.remove('award')

        if 'tags' in self._missing_fields:
            if row['has_tags']:
                self.anime.tags = {}
                c.execute('SELECT tag_id, tag_name, tag_weight FROM anime_tags WHERE aid = ?', (self.anime.aid,))
                for row in c:
                    self.anime.tags[row[0]] = AnimeTag(row[0], row[1], row[2])
                self._missing_fields.remove('tags')

        if 'characters' in self._missing_fields:
            if row['has_characters']:
                self.anime.characters = []
                c.execute('SELECT cid FROM anime_characters WHERE aid = ?', (self.anime.aid,))
                for row in c:
                    self.anime.characters.append(int(row[0]))
                self._missing_fields.remove('characters')

    def _read_from_anidb(self):
        pass

    def _write_to_cache(self):
        c = self.dbh.cursor()
        self.delete()
        c.execute('INSERT INTO anime (aid, updated) VALUES (?, ?)', (self.anime.aid, int(datetime.now().timestamp())))

        to_set = anime_info_fields.keys()

        for key in AnimeCache.fields_bool + AnimeCache.fields_int + AnimeCache.fields_str:
            if getattr(self.anime, key) is not None:
                to_set[key] = getattr(self.anime, key)
        for key in AnimeCache.fields_date:
            if getattr(self.anime, key) is not None:
                to_set[key] = int(getattr(self.anime, key).timestamp())

        q = 'UPDATE anime SET {} WHERE aid = ?'.format(map(lambda k: '`{}` = ?', to_set.keys()))
        c.execute(q, list(to_set.values()) + [self.anime.aid])

        for l in ('other', 'short', 'synonym'):
            names = getattr(self.anime, 'name_{}'.format(l))
            if names is not None and len(names):
                c.executemany('INSERT INTO anime_names (aid, name, name_type) VALUES (?, ?, ?)',
                              map(lambda n: (self.anime.aid, n, l), names))
            # noinspection SqlResolve
            c.execute('UPDATE anime SET has_name_{} = ? WHERE aid = ?'.format(l),
                      (int(names is not None), self.anime.aid,))

        if self.anime.awards is not None:
            c.executemany('INSERT INTO anime_awards (aid, award) VALUES (?, ?)',
                          map(lambda a: (self.anime.aid, a), self.anime.awards))

        if self.anime.characters is not None:
            c.executemany('INSERT INTO anime_characters (aid, cid) VALUES (?, ?)',
                          map(lambda a: (self.anime.aid, a,), self.anime.characters))

        if self.anime.related is not None:
            c.executemany('INSERT INTO anime_related (aid, related_aid, related_type) VALUES (?, ?, ?)',
                          map(lambda r: (self.anime.aid, r.related_id, r.related_type), self.anime.related))

        if self.anime.tags is not None:
            c.executemany('INSERT INTO anime_tags (aid, tag_id, tag_name, tag_weight) VALUES (?, ?, ?, ?)',
                          map(lambda t: (self.anime.aid, t.tag_id, t.tag_name, t.tag_weight), self.anime.tags))

        c.execute('UPDATE anime SET has_awards = ?, has_characters = ?, has_related = ?, has_tags = ? WHERE aid = ?', (
            int(self.anime.awards is not None),
            int(self.anime.characters is not None),
            int(self.anime.related is not None),
            int(self.anime.tags is not None),
            self.anime.aid
        ))

    def delete(self):
        c = self.dbh.cursor()
        aid = self.anime.aid
        c.execute('DELETE FROM anime_tags WHERE aid = ?', (aid,))
        c.execute('DELETE FROM anime_related WHERE aid = ?', (aid,))
        c.execute('DELETE FROM anime_names WHERE aid = ?', (aid,))
        c.execute('DELETE FROM anime_characters WHERE aid = ?', (aid,))
        c.execute('DELETE FROM anime_awards WHERE aid = ?', (aid,))
        c.execute('DELETE FROM anime WHERE aid = ?', (aid,))
