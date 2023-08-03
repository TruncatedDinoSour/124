#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124bot database models"""

import datetime
from json import dumps
from typing import Optional

import humanize  # type: ignore
import sqlalchemy

from . import const, sql

DB: sql.SQLiteDB = sql.SQLiteDB(const.BOT_DB_URL)


@DB.table
class Rule:
    id: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        autoincrement=True,
        nullable=False,
    )
    content: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
        unique=True,
        nullable=False,
    )
    real: sqlalchemy.Column[bool] = sqlalchemy.Column(sqlalchemy.Boolean)
    author: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    timestamp: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )

    def __init__(self, content: str, real: bool, author: int) -> None:
        # todo : make init gen cleaner and automatic

        self.content = content  # type: ignore
        self.real = real  # type: ignore
        self.author = author  # type: ignore
        self.timestamp = round(datetime.datetime.utcnow().timestamp())  # type: ignore


@DB.table
class ScoreKicks:
    author: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        nullable=False,
    )
    kicks: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )

    def __init__(self, author: int) -> None:
        self.author = author  # type: ignore
        self.kicks = 0  # type: ignore


@DB.table
class Score:
    author: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        nullable=False,
    )
    total_bytes: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    total_messages: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    vcs_joined: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    vcs_time: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    new_words: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    reactions_get: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    reactions_post: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    starboard_score: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    ok: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    last_act: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    stars_removed: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )

    def __init__(self, author: int) -> None:
        self.author = author  # type: ignore
        self.total_bytes = self.total_messages = self.vcs_joined = self.vcs_time = self.new_words = self.reactions_get = self.reactions_post = self.starboard_score = self.ok = self.stars_removed = 0  # type: ignore
        self.last_act = round(datetime.datetime.utcnow().timestamp())  # type: ignore

    def __str__(self) -> str:
        kick: Optional[tuple[int]] = (
            DB.query(ScoreKicks.kicks).where(ScoreKicks.author == self.author).first()  # type: ignore
        )

        return f"`{self.total_bytes}` b / `{self.total_messages}` msgs; `{self.vcs_time}` s \
( {humanize.precisedelta(datetime.timedelta(seconds=self.vcs_time), minimum_unit='seconds')} ) / `{self.vcs_joined}` vcs; \
`{self.new_words}` wordcloud words; `{self.reactions_get}` reac recv; `{self.reactions_post}` reac given; \
`{DB.query(Rule.id).where(Rule.author == self.author).count()}` rules; `{self.starboard_score}` stars; \
`{self.ok}` ok; last activity on `{str(datetime.datetime.utcfromtimestamp(self.last_act))} UTC`; \
`{self.stars_removed}` removed stars; `{0 if kick is None else kick[0]}` kicks"  # type: ignore


@DB.table
class WordCloud:
    word: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
        unique=True,
        nullable=False,
    )
    usage: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )

    def __init__(self, word: str) -> None:
        self.word = word  # type: ignore
        self.usage = 0  # type: ignore


@DB.table
class Confession:
    id: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        autoincrement=True,
        nullable=False,
    )
    content: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    timestamp: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )

    def __init__(self, content: str) -> None:
        self.content = content  # type: ignore
        self.timestamp = round(datetime.datetime.utcnow().timestamp())  # type: ignore


@DB.table
class StarBoard:
    id: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        nullable=False,
    )
    star_channel: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )
    starred_msgs: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
    )

    def __init__(self, id: int) -> None:
        self.id = id  # type: ignore
        self.starred_msgs = ""  # type: ignore


@DB.table
class MusicQueue:
    name: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
        unique=True,
        nullable=False,
    )
    queue: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
    )

    def __init__(self, name: str, queue: list[str]) -> None:
        self.name = name  # type: ignore
        self.queue = dumps(queue)  # type: ignore
