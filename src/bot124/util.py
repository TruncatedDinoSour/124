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
    if (
        s.vcs_joined == 0
        and s.reactions_get == 0
        and s.reactions_post == 0
        and s.new_words == 0
    ):
        return 0.0

    if (
        s.total_bytes is not None
        and s.total_messages is not None
        and s.total_messages > 0
    ):
        if s.total_bytes / s.total_messages >= const.LEN_FACTOR_THRESHOLD:
            len_factor: float = const.LEN_FACTOR_DIVISOR * const.LEN_MULTIPLIER
        else:
            len_factor: float = (
                s.total_bytes / s.total_messages
            ) / const.LEN_FACTOR_DIVISOR
    else:
        len_factor: float = const.LEN_FACTOR_DEF

    if s.vcs_joined > 0:
        if s.vcs_time / s.vcs_joined > const.VCS_FACTOR_THRESHOLD:
            vcs_factor: float = const.VCS_FACTOR_DIVISOR * 0.5
        else:
            vcs_factor: float = (s.vcs_time / s.vcs_joined) / const.VCS_FACTOR_DIVISOR
    else:
        vcs_factor: float = const.VCS_FACTOR_DEF

    return round(
        const.SCORE_MULT
        * (
            sum(
                stat * weight
                for stat, weight in zip(
                    (s.new_words, s.reactions_get + s.reactions_post),
                    (
                        const.NEW_WORDS_WEIGHT_MULTIPLIER,
                        const.REACTION_WEIGHT_MULTIPLIER,
                    ),
                )
                if stat > 0
            )
            / const.SCORE_DIVISOR
            * len_factor
            * vcs_factor
        )
        ** const.SCORE_COEFFICIENT,
        2,
    )
