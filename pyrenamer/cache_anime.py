from sqlite3 import connect, Row
from pyrenamer.config import cache_db
from time import time
from datetime import datetime

from pyrenamer import row_hash


class CacheAnime:
    fields_str = ('year', 'type', 'url', 'picname',)
    fields_int = (
        'episodes_count', 'episode_max', 'episodes_special_count', 'rating', 'vote_count', 'rating_temp',
        'vote_count_temp', 'review_rating', 'review_count', 'ann_id', 'allcinema_id', 'animenfo_id',
        'specials_count', 'credits_count', 'other_count', 'trailer_count', 'parody_count',
    )
    fields_date = ('date_air', 'date_end', 'record_updated',)
    fields_bool = ('is_restricted',)

    def __init__(self):
        self.dbh = connect(cache_db)
        self.dbh.row_factory = Row
        self._init_db()

    def _init_db(self):
        self.dbh.executescript('''
CREATE TABLE IF NOT EXISTS anime (
  aid INT NOT NULL PRIMARY KEY,
  date_flags INT,
  `year` TEXT,
  `type` TEXT,
  episodes_count INT,
  episode_max INT,
  episodes_special_count INT,
  date_air INT,
  date_end INT,
  url TEXT,
  picname TEXT,
  rating INT,
  vote_count INT,
  rating_temp INT,
  vote_count_temp INT,
  review_rating INT,
  review_count INT,
  is_restricted INT,
  ann_id INT,
  allcinema_id INT,
  animenfo_id INT,
  record_updated INT,
  specials_count INT,
  credits_count INT,
  other_count INT,
  trailer_count INT,
  parody_count INT,

  has_award INT,
  has_related INT,

  updated INT NOT NULL
);

CREATE TABLE IF NOT EXISTS anime_related (
  aid INT NOT NULL,
  related_aid INT NOT NULL,
  related_is_sequel INT,
  related_is_prequel INT,
  related_same_setting INT,
  related_alternative_setting INT,
  related_alternative_version INT,
  related_music_video INT,
  related_character INT,
  related_side_story INT,
  related_parent_story INT,
  related_summary INT,
  related_full_story INT,
  related_other INT
);
CREATE UNIQUE INDEX IF NOT EXISTS anime_related_aid ON anime_related (aid, related_aid);

CREATE TABLE IF NOT EXISTS anime_name (
  aid INT NOT NULL,
  `name` TEXT NOT NULL,
  name_type TEXT
);
CREATE INDEX IF NOT EXISTS anime_name_aid ON anime_name_other (aid, name_type);

CREATE TABLE IF NOT EXISTS anime_award (
  aid INT NOT NULL,
  award TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS anime_award_aid ON anime_award (aid);

CREATE TABLE IF NOT EXISTS anime_tags (
  aid INT NOT NULL,
  tag_id INT NOT NULL,
  tag_name text NOT NULL,
  tag_weight int
);
CREATE INDEX IF NOT EXISTS anime_tags_aid ON anime_tags (aid);

CREATE TABLE IF NOT EXISTS anime_character (
  aid INT NOT NULL,
  cid INT NOT NULL
);
CREATE INDEX IF NOT EXISTS anime_character_aid ON anime_character (aid, cid);
CREATE INDEX IF NOT EXISTS anime_character_cid ON anime_character (cid, aid);
        ''')

    def get(self, aid, fields, max_age=None):
        c = self.dbh.cursor()
        if max_age is None:
            c.execute('SELECT * FROM anime WHERE aid = ?', (aid,))
        else:
            c.execute('SELECT * FROM anime WHERE aid = ? AND updated > ?', (aid, time() - max_age))
        row = c.fetchone()
        if not row:
            return None

        result = {'updated': row[0], 'aid': aid}
        row = row_hash(c, row)
        if 'date_flags' in fields:
            date_flags = row['data_flags']
            result['date_flags'] = {
                'start_unknown_day': date_flags & 0x80,
                'start_unknown_month': date_flags & 0x40,
                'end_unknown_day': date_flags & 0x20,
                'end_unknown_month': date_flags & 0x10,
                'has_ended': date_flags & 0x8,
                'start_unknown_year': date_flags & 0x4,
                'end_unknown_year': date_flags & 0x2
            }
        for field in fields:
            if field in CacheAnime.fields_str or field in CacheAnime.fields_int or field in CacheAnime.fields_bool or field in CacheAnime.fields_date:
                result[field] = c.execute('SELECT `{}` FROM anime WHERE aid = ?'.format(field), (aid,)).fetchone()[
                    0]
            if field in CacheAnime.fields_int and result[field] is not None:
                result[field] = int(result[field])
            if field in CacheAnime.fields_bool and result[field] is not None:
                result[field] = bool(result[field])
            if field in CacheAnime.fields_date and result[field] is not None:
                result[field] = datetime.fromtimestamp(result[field])

        if 'name' in fields:
            c.execute('SELECT `name`, name_type FROM anime_name WHERE aid = ?', (aid,))
            if c.rowcount == 0:
                result['name'] = None
            else:
                result['name'] = {}
                for row in c:
                    if row[1] in ('romaji', 'kanji', 'english'):
                        result['name'][row[1]] = row[0]
                    elif row[1] in ('other', 'short', 'synonym'):
                        if result['name'][row[1]] is None:
                            result['name'][row[1]] = []
                        result['name'][row[1]].append(row[0])

        if 'related' in fields:
            c.execute('SELECT has_related FROM anime WHERE aid = ?', (aid,))
            if not c.fetchone()[0]:
                result['related'] = None
            else:
                c.execute('SELECT * FROM related WHERE aid = ?', (aid,))
                result['related'] = {}
                for row in c:
                    result['related'][row[0]] = {
                        'aid': int(row[1]),
                        'is_sequel': bool(row[2]),
                        'is_prequel': bool(row[3]),
                        'same_setting': bool(row[4]),
                        'alternative_setting': bool(row[5]),
                        'alternative_version': bool(row[6]),
                        'music_video': bool(row[7]),
                        'character': bool(row[8]),
                        'side_story': bool(row[9]),
                        'parent_story': bool(row[10]),
                        'summary': bool(row[11]),
                        'full_story': bool(row[12]),
                        'other': bool(row[13])
                    }

        if 'award' in fields:
            c.execute('SELECT has_award FROM anime WHERE aid = ?', (aid,))
            if not c.fetchone()[0]:
                result['award'] = None
            else:
                c.execute('SELECT award FROM anime_award WHERE aid = ?', (aid,))
                result['award'] = []
                for row in c:
                    result['award'].append(row[0])
