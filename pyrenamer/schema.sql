CREATE TABLE IF NOT EXISTS cache (
  `key` TEXT NOT NULL,
  value TEXT NOT NULL,
  created INT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS cache_key ON cache (key);



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

  has_tags INT,
  has_name_romaji INT,
  has_name_kanji INT,
  has_name_english INT,
  has_name_other INT,
  has_name_short INT,
  has_name_synonym INT,
  has_award INT,
  has_related INT,
  has_characters INT,

  updated INT NOT NULL
);

CREATE TABLE IF NOT EXISTS anime_related (
  aid INT NOT NULL,
  related_aid INT NOT NULL,
  related_type INT,
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
