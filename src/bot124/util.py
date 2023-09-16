#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""random bot utilities"""

import asyncio
import math
import typing
from datetime import datetime

import aiohttp
from discord import User

from . import const, models


def get_score(id: int) -> models.Score:
    sql_obj: models.Score = (
        models.DB.query(models.Score).where(models.Score.author == id).first()  # type: ignore
    )

    if sql_obj is None:
        models.DB.add(sql_obj := models.Score(author=id))

    models.DB.commit()
    return sql_obj


def get_starboard(id: int) -> models.StarBoard:
    sql_obj: models.StarBoard = (
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
    kick: models.ScoreKicks = (
        models.DB.query(models.ScoreKicks).where(models.ScoreKicks.author == s.author).first()  # type: ignore
    )

    score: float = max(
        0,
        (
            s.total_bytes
            + s.total_messages
            + (s.total_bytes / max(s.total_messages, 1))
            + ((s.vcs_time / max(s.vcs_joined, 1)) * const.SCORE_VCS_AVG_W)
            + (math.log2(s.vcs_time + 1) * const.SCORE_VCS_TIME_W)
            + (math.log2(s.new_words + 1) / const.SCORE_NEW_WORDS_D)
            + s.reactions_get
            - (s.reactions_post / const.SCORE_REACTIONS_POST_D)
            + (s.starboard_score * const.SCORE_STARBOARD_W)
            + math.log(s.ok + 1)
            - ((datetime.utcnow().timestamp() - s.last_act) ** const.SCORE_TIME_E)
            - (s.stars_removed * const.SCORE_STAR_RM_W)
            + (s.stars_participated / const.SCORE_STAR_P_D)
            - const.SCORE_BAR
        )
        * const.SCORE_W,
    ) / ((kick.kicks + 1) if kick is not None else 1)

    return round(score**const.SCORE_E, 2)


def update_act(id: int) -> None:
    get_score(id).last_act = round(datetime.utcnow().timestamp())
    models.DB.commit()


async def get_proxies() -> dict[str, str]:
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(const.PROXY_API) as resp:
                proxy: str = await resp.text()

            try:
                async with session.get(
                    const.PROXY_TEST,
                    timeout=const.PROXY_TIMEOUT,
                    proxy=proxy,
                ) as resp:
                    if not resp.ok:
                        raise Exception("proxy failed")
            except Exception:
                await asyncio.sleep(1)
                continue

            return {"proxy": proxy}
