#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""random bot utilities"""

import typing
from datetime import datetime
from math import log

from discord import User

from . import const, models


def get_score(id: int) -> models.Score:
    sql_obj: typing.Any = (
        models.DB.query(models.Score).where(models.Score.author == id).first()
    )

    if sql_obj is None:
        models.DB.add(sql_obj := models.Score(author=id))

    return sql_obj


def datetime_s(ts: int) -> str:
    return datetime.utcfromtimestamp(ts).strftime("%Y/%m/%d %H:%M")


def word_count(lst: typing.Iterable[str]) -> dict[str, int]:
    word_dict: dict[str, int] = {}

    for word in lst:
        if word in word_dict:
            word_dict[word] += 1
        else:
            word_dict[word] = 1

    return word_dict


def filter_rule_like(
    model: typing.Any,
    id: typing.Optional[int] = None,
    yyyymmddhh_before: typing.Optional[str] = None,
    yyyymmddhh_after: typing.Optional[str] = None,
) -> typing.Any:  # type: ignore
    q: typing.Any = models.DB.query(model)

    if id is not None:
        q = q.filter(model.id == id)

    try:
        if yyyymmddhh_before is not None:
            q = q.filter(
                model.timestamp
                <= datetime.strptime(yyyymmddhh_before, "%Y%m%d%H").timestamp()
            )

        if yyyymmddhh_after is not None:
            q = q.filter(
                model.timestamp
                >= datetime.strptime(yyyymmddhh_after, "%Y%m%d%H").timestamp()
            )
    except ValueError:
        return "invalid datetime format for yyyymmmddhh* arguments, keep in mind the format is yyyymmmddhh, so ***2023011023*** = 2023/01/10 23:00"

    return q


def filter_rules(
    id: typing.Optional[int] = None,
    real: typing.Optional[bool] = None,
    user: typing.Optional[User] = None,
    yyyymmddhh_before: typing.Optional[str] = None,
    yyyymmddhh_after: typing.Optional[str] = None,
) -> typing.Any:  # type: ignore
    q: typing.Any = filter_rule_like(
        models.Rule, id, yyyymmddhh_before, yyyymmddhh_after
    )

    if real is not None:
        q = q.filter(models.Rule.real == real)

    if user is not None:
        q = q.filter(models.Rule.author == user.id)

    return q


def calc_score(s: models.Score) -> float:
    return round(
        const.MSGS_WEIGHT * (s.total_messages / (s.total_messages + s.total_bytes + 1))
        + const.BYTES_WEIGHT * (s.total_bytes / (s.total_messages + s.total_bytes + 1))
        + const.VC_JOIN_WEIGHT * (s.vcs_joined / (s.total_messages + s.vcs_joined + 1))
        + const.VC_TIME_WEIGHT * (s.vcs_time / (s.vcs_joined + s.vcs_time + 1))
        + const.NEW_WORDS_WEIGHT
        * log(models.DB.query(models.WordCloud.word).count() + 1)  # type: ignore
        * s.new_words
        + const.REACTIONS_POST_WEIGHT
        * min(s.reactions_post / max(s.reactions_get, 1), 1)
        + const.REACTIONS_GET_WEIGHT
        * (s.reactions_get / (s.total_messages + 1))
        * const.SCORE_MULT,
        2,
    )
