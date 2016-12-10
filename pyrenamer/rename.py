anime_info_fields = dict(
    date_flags=False,
    year=False,
    type=False,
    url=False,
    picname=False,

    episodes_count=False,
    episode_max=False,
    episodes_special_count=False,

    rating=False,
    vote_count=False,
    rating_temp=False,
    vote_count_temp=False,
    review_rating=False,
    review_count=False,

    ann_id=False,
    allcinema_id=False,
    animenfo_id=False,

    specials_count=False,
    credits_count=False,
    other_count=False,
    trailter_count=False,
    parody_count=False,
    date_air=False,
    date_end=False,

    is_restricted=True,

    related=False,

    name_romaji=True,
    name_kanji=False,
    name_english=True,
    name_other=False,
    name_short=False,
    name_synonym=False,

    awards=False,

    tags=False,

    characters=False
)

file_info_fields = dict(
    gid=False,  # enable fetching the group info
    mylist_id=True,
    other_episodes=False,
    state=False,
    size=False,
    ed2k=False,
    md5=False,
    sha1=False,
    crc32=True,
    video_colour_depth=False,
    quality=False,
    source=False,
    audio=False,
    video=False,
    file_type=False,
    dub_language=True,
    sub_language=True,
    length=False,
    description=False,
    aired=False,
    anidb_file_name=False,
    mylist_state=False,
    mylist_filestate=False,
    mylist_viewed=False,
    mylist_viewdate=False,
    mylist_storage=False,
    mylist_source=False,
    mylist_other=False,

    anime_total_episodes=False,
    anime_highest_episode=False,
    year=False,
    type=False,
    related=False,
    category=False,

    name_romaji=False,
    name_kanji=False,
    name_english=False,
    name_other=False,
    name_short=False,
    name_synonym=False,

    ep_number=False,
    ep_name=False,
    ep_name_romaji=False,
    ep_name_kanji=False,
    episode_rating=False,
    episode_vote_count=False,
    group_name=False,
    group_short_name=True
)


def rename(file_info, anime_info, group_info):
    """

    :param pyrenamer.file.File file_info: The file info for the file
    :param pyrenamer.anime.Anime anime_info: The anime info for the file
    :param pyrenamer.group.Group group_info: The group info for the file
    :return: The new relative file name
    :rtype: str
    """
    pass
