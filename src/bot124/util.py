#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""random bot utilities"""

import math
import typing
from datetime import datetime

from discord import User

from . import const, models


def get_score(id: int) -> models.Score:
    sql_obj: typing.Any = (
        models.DB.session.query(models.Score).where(models.Score.author == id).first()
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
    q: typing.Any = models.DB.session.query(model)

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
    # honestly this is purely obscurity lol, these constants mean nothing,
    # just obscure underlying ratio lol

    return round(
        (
            (
                (
                    (s.total_messages / (s.total_bytes + 1))
                    + (s.total_bytes / (s.total_messages + 1))
                    + (s.vcs_joined + (s.vcs_time + 1))
                    + (s.vcs_time + (s.vcs_joined + 1))
                )
                / const.GOLDEN_RATIO
            )
            * math.pi
        )
        + (1 / 90),
        2,
    )
