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
        models.DB.query(models.Score).where(models.Score.author == id).first()  # type: ignore
    )

    if sql_obj is None:
        models.DB.add(sql_obj := models.Score(author=id))

    models.DB.commit()
    return sql_obj


def get_starboard(id: int) -> models.StarBoard:
    sql_obj: typing.Any = (
        models.DB.query(models.StarBoard).where(models.StarBoard.id == id).first()  # type: ignore
    )

    if sql_obj is None:
        models.DB.add(sql_obj := models.StarBoard(id=id))

    models.DB.commit()
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
    q: typing.Any = models.DB.query(model)  # type: ignore

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
    score: float = max(
        0,
        const.SCORE_MULT
        * (
            s.total_bytes / (s.total_messages + 1) * const.MSGS_W
            + s.vcs_time / (s.vcs_joined + 1) * const.VCS_W
            + s.new_words * const.WC_W
            + math.sqrt(s.reactions_get) * const.REACT_GET_W
            + math.log2(
                models.DB.query(models.Rule.id)  # type: ignore
                .where(models.Rule.author == s.author)
                .count()
                + 1
            )
            + math.log(s.ok + 1) * const.OK_W
            + s.starboard_score * const.STAR_W
            - math.sqrt(s.reactions_post * const.REACT_POST_K) * const.REACT_POST_W
        ),
    )

    data: tuple[int] = tuple(
        v for k, v in s.__dict__.items() if k[0] != "_" and "_" in k
    )

    k: float = len(data) / sum(data) * const.K_MULT

    return round((score if k > score else score - k) ** const.SCORE_E, 2)
