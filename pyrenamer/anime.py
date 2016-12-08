class Anime:
    def __init__(self, aid):
        self.aid = aid
        self.date_flags = None
        self.year = None
        self.type = None
        self.url = None
        self.picname = None
        self.episodes_count = None
        self.episode_max = None
        self.episodes_special_count = None
        self.rating = None
        self.vote_count = None
        self.rating_temp = None
        self.vote_count_temp = None
        self.review_rating = None
        self.review_count = None
        self.ann_id = None
        self.allcinema_id = None
        self.animenfo_id = None
        self.specials_count = None
        self.credits_count = None
        self.other_count = None
        self.trailer_count = None
        self.parody_count = None
        self.date_air = None
        self.date_end = None
        self.record_updated = None
        self.is_restricted = None

        self.related = None
        """ :type: list[AnimeRelated]|None """
        self.name = AnimeName()
        self.award = None
        """ :type: list[str]|None """
        self.tags = None
        """ :type: list[AnimeTag]|None """
        self.characters = None
        """ :type: list[int]|None """

        self.updated = None

    @property
    def start_unknown_day(self):
        return self.date_flags is None or self.date_flags & 0x80

    @property
    def start_unknown_month(self):
        return self.date_flags is None or self.date_flags & 0x40

    @property
    def end_unknown_day(self):
        return self.date_flags is None or self.date_flags & 0x20

    @property
    def end_unknown_month(self):
        return self.date_flags is None or self.date_flags & 0x10

    @property
    def has_ended(self):
        return self.date_flags is None or self.date_flags & 0x08

    @property
    def start_unknown_year(self):
        return self.date_flags is None or self.date_flags & 0x04

    @property
    def end_unknown_year(self):
        return self.date_flags is None or self.date_flags & 0x02


class AnimeName:
    def __init__(self):
        self.romaji = None
        self.kanji = None
        self.english = None
        self.other = None
        self.short = None
        self.synonym = None


class AnimeRelated:
    def __init__(self, related_id=None, related_type=None):
        self.related_id = related_id
        self.related_type = related_type

    @property
    def related_type_text(self):
        if self.related_type is None:
            return 'UNKNOWN'
        return {
            1: 'sequel',
            2: 'prequel',
            11: 'same_setting',
            12: 'alternative_setting',
            32: 'alternative_version',
            41: 'music_video',
            42: 'character',
            51: 'side_story',
            52: 'parent_story',
            61: 'summary',
            62: 'full_story',
            100: 'other'
        }.get(int(self.related_type))


class AnimeTag:
    def __init__(self, tag_id=None, tag_name=None, tag_weight=None):
        self.tag_id = tag_id
        self.tag_name = tag_name
        self.tag_weight = tag_weight
