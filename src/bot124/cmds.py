#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bot 124 commands"""

import typing

import discord
import discord.app_commands  # type: ignore
import sqlalchemy

from . import const, menu, models, util
from .cmdmgr import CommandManager

__all__: tuple[str] = ("cmds",)

cmds: CommandManager = CommandManager()


@cmds.new
async def status(
    msg: discord.interactions.Interaction,
    value: typing.Optional[str] = None,
    type: discord.ActivityType = discord.ActivityType.playing,
) -> None:  # type: ignore
    """set or reset bots 'playing' status"""

    await msg.response.defer()

    if value is not None:
        value = value[: const.MAX_PRESENCE_LEN].strip()

    await cmds.b.change_presence(
        activity=None
        if (
            reset := value is None
            or type in (discord.ActivityType.unknown, discord.ActivityType.custom)
        )
        else discord.Activity(name=value, type=type)
    )

    await msg.followup.send(
        content="i am no longer doing anything"
        if reset
        else f"i am now `{type.name} {value}`"
    )


@cmds.new
async def rules(
    msg: discord.interactions.Interaction,
    query: typing.Optional[str] = None,
    id: typing.Optional[int] = None,
    real: typing.Optional[bool] = None,
    user: typing.Optional[discord.User] = None,
    yyyymmddhh_before: typing.Optional[str] = None,
    yyyymmddhh_after: typing.Optional[str] = None,
    limit: int = const.MIN_RULES_LIMIT,
) -> None:  # type: ignore
    """get rules by filter and / or query"""

    q: typing.Any = util.filter_rules(
        id=id,
        real=real,
        user=user,
        yyyymmddhh_before=yyyymmddhh_before,
        yyyymmddhh_after=yyyymmddhh_after,
    )

    if type(q) is str:
        await msg.response.defer()
        await msg.followup.send(content=q)
        return

    q = q.limit(limit)

    q = (
        q.all()
        if query is None
        else tuple(r for r in q.all() if r.content in query or query in r.content)
    )

    rules: str = (
        f"rules ( {len(q)}/{models.DB.query(models.Rule.id).count()} result( s ) ) :\n\n"
        if id is None
        else ""
    )

    for r in q:
        rules += f"{r.id}, {r.content} ( {'real' if r.real else 'fake'} rule ) by <@{r.author}> on {util.datetime_s(r.timestamp)}\n"

    await menu.text_menu(msg, rules)


@cmds.new
async def lb(msg: discord.interactions.Interaction) -> None:  # type: ignore
    """rules leaderboard by rule creation count"""

    lb: typing.Dict[int, int] = {}

    for (author,) in models.DB.query(
        sqlalchemy.distinct(models.Rule.author)
    ).all():
        lb[author] = (
            models.DB.query(sqlalchemy.distinct(models.Rule.id))
            .where(models.Rule.author == author)
            .count()
        )

    lb: dict[int, int] = {
        k: v for k, v in sorted(lb.items(), key=lambda item: item[1], reverse=True)
    }
    total: int = sum(lb.values())

    await menu.text_menu(
        msg,
        "rules leaderboard :\n\n"
        + "".join(
            f"{rank}, <@{id}> with {count} ( {(count / total * 100):.2f}% ) created rule( s )\n"
            for rank, (id, count) in enumerate(lb.items(), 1)
        )
        + f"\n{total} rule( s ) in total",
    )


@cmds.new
async def score(msg: discord.interactions.Interaction, user: typing.Optional[discord.user.User] = None) -> None:  # type: ignore
    """get your or other users' chat score chat score"""

    if user is not None and user.bot:
        await menu.text_menu(msg, "bots cannot have scores")
        return

    score: typing.Any = (
        models.DB.query(models.Score)
        .where(models.Score.author == (msg.user.id if user is None else user.id))  # type: ignore
        .first()
    )

    await menu.text_menu(
        msg,
        (("you have" if user is None else f"{user.mention} has") + " no score")
        if score is None
        else "the chat score for "
        + ("you" if user is None else user.mention)
        + f" is `{util.calc_score(score)}` ( {score} )",
    )


@cmds.new
async def scores(msg: discord.interactions.Interaction) -> None:  # type: ignore
    """get chat scores"""

    scores: typing.Any = models.DB.query(models.Score).all()

    if not scores:
        await menu.text_menu(msg, "no people currently have a score")
        return

    lb: dict[int, int] = dict(
        sorted(  # type: ignore
            {s.author: util.calc_score(s) for s in scores}.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )
    lbv: tuple[int] = tuple(lb.values())
    total_lbv: int = sum(lbv)

    await menu.text_menu(
        msg,
        "chat score leaderboard :\n\n"
        + "\n".join(
            f"{idx}, <@{value[0]}> with score `{value[1]}`"
            for idx, value in enumerate(lb.items(), 1)
        )
        + f"\n\naverage chat score : {total_lbv / len(lbv):.2f}\ntotal chat score : {total_lbv:.2f}",
    )


@cmds.new
async def wordcloud(
    msg: discord.interactions.Interaction,
    limit: int = const.MIN_WORDCLOUD_LIMIT,
    usage_lt: typing.Optional[int] = None,
    usage_mt: typing.Optional[int] = None,
    query: typing.Optional[str] = None,
) -> None:  # type: ignore
    """get the word cloud by filter, limit and query"""

    q: typing.Any = models.DB.query(models.WordCloud).order_by(
        models.WordCloud.usage.desc()
    )

    if usage_lt is not None:
        q = q.where(models.WordCloud.usage <= usage_lt)

    if usage_mt is not None:
        q = q.where(models.WordCloud.usage >= usage_mt)

    q = q.limit(limit)

    if query is not None:
        query = query.lower()

    q = (
        q.all()
        if query is None
        else tuple(r for r in q.all() if r.word in query or query in r.word)
    )

    ql: int = len(q)

    await menu.text_menu(
        msg,
        f"word cloud ( {ql}/{models.DB.query(models.WordCloud.usage).count()} word( s ) )\n\n"
        + (
            "".join(
                f"{idx}, {w.word} ( {w.usage} ( {w.usage / ql * 100:.2f}% ) )\n"
                for idx, w in enumerate(q, 1)
            )
        ),
        const.WORDCLOUD_WRAP,
    )


@cmds.new
async def confess(
    msg: discord.interactions.Interaction,
    content: str,
) -> None:  # type: ignore
    """add an anonymous confession"""

    await msg.response.defer(ephemeral=True)
    models.DB.add(
        (sql_obj := models.Confession(content=content[: const.MESSAGE_WRAP_LEN]))
    )
    await msg.followup.send(content=f"saved confession #{sql_obj.id}", ephemeral=True)


@cmds.new
async def confessions(
    msg: discord.interactions.Interaction,
    query: typing.Optional[str] = None,
    id: typing.Optional[int] = None,
    yyyymmddhh_before: typing.Optional[str] = None,
    yyyymmddhh_after: typing.Optional[str] = None,
    limit: int = const.MIN_CONFESSION_LIMIT,
) -> None:  # type: ignore
    """view, list and filter confessions"""

    q: typing.Any = util.filter_rule_like(
        models.Confession, id, yyyymmddhh_before, yyyymmddhh_after
    ).limit(limit)

    q = (
        q.all()
        if query is None
        else tuple(c for c in q.all() if c.content in query or query in c.content)
    )

    confession_count: int = models.DB.query(models.Confession.id).count()

    await menu.menu(
        msg,
        tuple(
            f"*confession #{c.id}, {len(q)}/{confession_count} result( s ) on {util.datetime_s(c.timestamp)}*\n\n{c.content}"
            for c in q
        ),
    )
