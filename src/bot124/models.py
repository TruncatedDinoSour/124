#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124bot database models"""

import datetime

import humanize
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
    )
    content: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
        unique=True,
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
class Score:
    author: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
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

    def __init__(self, author: int) -> None:
        self.author = author  # type: ignore
        self.total_bytes = self.total_messages = self.vcs_joined = self.vcs_time = 0  # type: ignore

    def __str__(self) -> str:
        return f"`{self.total_bytes}` b / `{self.total_messages}` msgs; `{self.vcs_time}` s ( {humanize.precisedelta(datetime.timedelta(seconds=self.vcs_time), minimum_unit='seconds')} ) / `{self.vcs_joined}` vcs"


@DB.table
class WordCloud:
    word: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
        unique=True,
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
    )
    content: sqlalchemy.Column[str] = sqlalchemy.Column(
        sqlalchemy.String,
    )
    timestamp: sqlalchemy.Column[int] = sqlalchemy.Column(
        sqlalchemy.Integer,
    )

    def __init__(self, content: str) -> None:
        self.content = content  # type: ignore
        self.timestamp = round(datetime.datetime.utcnow().timestamp())  # type: ignore
