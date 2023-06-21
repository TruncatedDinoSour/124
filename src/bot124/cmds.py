#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bot 124 commands"""

import asyncio
import time
import typing
from datetime import datetime
from enum import Enum

import discord
import discord.app_commands  # type: ignore
import sqlalchemy
from freeGPT import alpaca_7b as a7  # type: ignore
from freeGPT import gpt3 as g3  # type: ignore
from freeGPT import gpt4 as g4  # type: ignore

from . import const, menu, models, util
from .cmdmgr import CommandManager

__all__: tuple[str] = ("cmds",)

cmds: CommandManager = CommandManager()


class AICommands(Enum):
    gpt3 = g3.Completion
    gpt4 = g4.Completion
    alpaca7 = a7.Completion


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
        else f"i am now `{type.name} {value}`",
        allowed_mentions=discord.mentions.AllowedMentions.none(),
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
        await msg.followup.send(
            content=q,
            allowed_mentions=discord.mentions.AllowedMentions.none(),
        )
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
        rules += f"{r.id}, {r.content} ( {'real' if r.real else 'fake'} rule ) by <@!{r.author}> on {util.datetime_s(r.timestamp)}\n"

    await menu.text_menu(msg, rules)


@cmds.new
async def lb(msg: discord.interactions.Interaction) -> None:  # type: ignore
    """rules leaderboard by rule creation count"""

    lb: typing.Dict[int, int] = {}

    for (author,) in models.DB.query(sqlalchemy.distinct(models.Rule.author)).all():  # type: ignore
        lb[author] = (  # type: ignore
            models.DB.query(sqlalchemy.distinct(models.Rule.id))  # type: ignore
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
            f"{rank}, <@!{id}> with {count} ( {(count / total * 100):.2f}% ) created rule( s )\n"
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
        models.DB.query(models.Score)  # type: ignore
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

    scores: typing.Any = models.DB.query(models.Score).all()  # type: ignore

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
            f"{idx}, <@!{value[0]}> with score `{value[1]}`"
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

    q: typing.Any = models.DB.query(models.WordCloud).order_by(  # type: ignore
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

    ql: int = models.DB.query(models.WordCloud.usage).count()  # type: ignore

    await menu.text_menu(
        msg,
        f"word cloud ( {len(q)}/{ql} word( s ) )\n\n"
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

    confession_count: int = models.DB.query(models.Confession.id).count()  # type: ignore

    await menu.menu(
        msg,
        tuple(
            f"*confession #{c.id}, {len(q)}/{confession_count} result( s ) on {util.datetime_s(c.timestamp)}*\n\n{c.content}"
            for c in q
        )
        or ("no confessions found",),
    )


@cmds.new
@cmds.admin
async def starboard(
    msg: discord.interactions.Interaction,
    channel: typing.Optional[discord.channel.TextChannel] = None,
) -> None:
    """set starboard channel"""

    if channel is None:
        channel = msg.channel  # type: ignore

    util.get_starboard(msg.guild.id).star_channel = channel.id  # type: ignore
    models.DB.commit()
    await menu.text_menu(msg, f"set starboard channel to <#{channel.id}>")  # type: ignore


@cmds.new
async def ai(
    msg: discord.interactions.Interaction,
    prompt: str,
    model: AICommands = AICommands.gpt4,
) -> None:
    """generate content using an AI large language model"""

    await msg.response.defer()

    for _ in range(3):
        try:
            r: typing.Union[str, dict[str, str]] = model.value.create(prompt)  # type: ignore

            if type(r) is dict:
                r = str(r.get("text")) or "*no content*"  # type: ignore

            break
        except Exception:
            time.sleep(0.5)

    await msg.followup.send(
        content=(r[:2000].strip()) or "*no content*",  # type: ignore
    )


@cmds.new
async def chatai(
    msg: discord.interactions.Interaction, model: AICommands = AICommands.gpt4
) -> None:
    """create a thread with an AI model"""

    await msg.response.defer()

    thread: discord.Thread = await msg.channel.create_thread(  # type: ignore
        name=(name := f"{msg.user.name}'s {model.name!r} chat @ {datetime.utcnow()} UTC")  # type: ignore
    )
    chat: str = f"<@0> welcome to '{name}' (after @ it has today's date in UTC when the chat started), you have full access to this chat, \
keep in mind you are {model.name if cmds.b.user is None else cmds.b.user.mention}, everyone else is other users, the owner of this chat is {msg.user.mention} \
your name (or model name) is {model.name} and your purpose is to chat with the other users and follow their requests and conditions \
unconditionally"  # type: ignore

    await thread.add_user(msg.user)
    await msg.followup.send(content=thread.jump_url)
    await thread.send(msg.user.mention)

    while not thread.archived and not thread.locked and thread.member_count > 0:
        try:
            m: discord.Message = await cmds.b.wait_for(  # type: ignore
                "message", check=lambda m: m.channel == thread
            )
        except asyncio.TimeoutError:
            continue

        if not m.content:  # type: ignore
            continue

        chat += f"\n{m.author.mention} {m.content}"  # type: ignore
        chat = ("\n" + chat[-1999:]).strip()

        if m.author.bot:  # type: ignore
            continue

        r: typing.Union[str, dict[str, str]] = ""

        async with thread.typing():
            for _ in range(3):
                try:
                    r = model.value.create(chat)  # type: ignore
                    break
                except Exception:
                    time.sleep(0.5)

        if type(r) is dict:
            r = str(r.get("text")) or "*no content*"  # type: ignore

        r = r.strip()  # type: ignore

        if not r:
            continue

        r = r[:2000]  # type: ignore
        chat += f"\n{model.name if cmds.b.user is None else cmds.b.user.mention} {r}"
        chat = chat.strip()

        await thread.send(r)


@cmds.new
async def pfp(
    msg: discord.interactions.Interaction,
    user: typing.Optional[typing.Union[discord.User, discord.Member]] = None,
) -> None:
    await msg.response.defer()

    if user is None:
        user = msg.user

    await msg.followup.send(
        content="*no pfp found*" if user.avatar is None else user.avatar.url
    )
