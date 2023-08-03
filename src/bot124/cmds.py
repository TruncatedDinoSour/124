#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bot 124 commands"""

import asyncio
import datetime
import time
import typing
from enum import Enum, auto
from io import BytesIO
from secrets import SystemRandom
from subprocess import check_output

import discord
import discord.app_commands  # type: ignore
import humanize  # type: ignore
import requests
import sqlalchemy
from discord.ui import Button, View
from freeGPT import alpaca_7b as a7  # type: ignore
from freeGPT import gpt3 as g3  # type: ignore
from freeGPT import gpt4 as g4  # type: ignore
from freeGPT import prodia as pr  # type: ignore

from . import const, menu, models
from . import music as music_mdl
from . import util
from .cmdmgr import CommandManager

__all__: tuple[str] = ("cmds",)

cmds: CommandManager = CommandManager()
RAND: SystemRandom = SystemRandom()


class TextAICommands(Enum):
    gpt3 = g3.Completion
    gpt4 = g4.Completion
    alpaca7 = a7.Completion


async def gen_ai_text(prompt: str, model: TextAICommands = TextAICommands.gpt3) -> str:
    r: typing.Union[str, dict[str, str]] = ""

    for _ in range(3):
        try:
            r: typing.Union[str, dict[str, str]] = await model.value.create(prompt)  # type: ignore

            if type(r) is dict:
                r = str(r.get("text")) or "*no content*"  # type: ignore

            break
        except Exception:
            time.sleep(0.5)

    return r[:2000].strip()  # type: ignore


class FakeProdia(pr.Generation):
    pass


class ImageAICommands(Enum):
    prodia = pr.Generation
    fake_prodia = FakeProdia


async def gen_ai_img(
    prompt: str, model: ImageAICommands = ImageAICommands.prodia
) -> discord.File:
    r: BytesIO = BytesIO()

    for _ in range(3):
        try:
            r: BytesIO = await model.value.create(prompt)  # type: ignore
            break
        except Exception:
            time.sleep(0.5)

    return discord.File(
        r,
        f"{cmds.b.user.name if cmds.b.user else 124}_{model.name}_generation_{datetime.datetime.utcnow()}.png",
    )


class TruthOrDare(Enum):
    random = auto()
    truth = const.TRUTHS
    dare = const.DARES
    paranoia = const.PARANOIAS


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
async def ruleslb(msg: discord.interactions.Interaction) -> None:  # type: ignore
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
async def scorelb(msg: discord.interactions.Interaction) -> None:  # type: ignore
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
            f"{idx}, <@{value[0]}> with score `{value[1]}`"
            for idx, value in enumerate(lb.items(), 1)
        )
        + f"\n\naverage chat score : {total_lbv / len(lbv):.2f}\ntotal chat score : {total_lbv:.2f}",
    )


@cmds.new
async def wordcloud(
    msg: discord.interactions.Interaction,
    usage_lt: typing.Optional[int] = None,
    usage_mt: typing.Optional[int] = None,
    query: typing.Optional[str] = None,
) -> None:  # type: ignore
    """get the word cloud by filter and query"""

    q: typing.Any = models.DB.query(models.WordCloud).order_by(  # type: ignore
        models.WordCloud.usage.desc()
    )

    if usage_lt is not None:
        q = q.where(models.WordCloud.usage <= usage_lt)

    if usage_mt is not None:
        q = q.where(models.WordCloud.usage >= usage_mt)

    if query is not None:
        query = query.lower()

    q = (
        q.all()
        if query is None
        else tuple(r for r in q.all() if r.word in query or query in r.word)
    )

    ql: int = models.DB.query(models.WordCloud.usage).count()  # type: ignore
    qa: int = models.DB.query(sqlalchemy.func.sum(models.WordCloud.usage)).scalar()  # type: ignore

    await menu.text_menu(
        msg,
        f"word cloud ( {len(q)}/{ql} unique word( s )/{qa} used words )\n{qa / ql:.2f} uses per word per avg\n\n"
        + (
            "".join(
                f"{idx}, {w.word} ( {w.usage} ( {w.usage / qa * 100:.2f}% ) )\n"
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
) -> None:  # type: ignore
    """view, list and filter confessions"""

    q: typing.Any = util.filter_rule_like(
        models.Confession, id, yyyymmddhh_before, yyyymmddhh_after
    )

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
    model: TextAICommands = TextAICommands.gpt3,
) -> None:
    """generate content using an AI large language model"""

    await msg.response.defer()

    await msg.followup.send(
        content=(await gen_ai_text(prompt, model)) or "*no content*",  # type: ignore
    )


@cmds.new
async def aiimg(
    msg: discord.interactions.Interaction,
    prompt: str,
    model: ImageAICommands = ImageAICommands.prodia,
) -> None:
    """generate content using an AI image model"""

    await msg.response.defer()

    await msg.followup.send(file=await gen_ai_img(prompt, model))


@cmds.new
async def chatai(
    msg: discord.interactions.Interaction, model: TextAICommands = TextAICommands.gpt3
) -> None:
    """create a thread with an AI model"""

    await msg.response.defer()

    thread: discord.Thread = await msg.channel.create_thread(  # type: ignore
        name=(name := f"{msg.user.name}'s {model.name!r} chat @ {datetime.datetime.utcnow()} UTC")  # type: ignore
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
            r = await gen_ai_text(chat, model)

        if not r:
            continue

        chat += f"\n{model.name if cmds.b.user is None else cmds.b.user.mention} {r}"
        chat = chat.strip()

        await thread.send(r)


@cmds.new
async def pfp(
    msg: discord.interactions.Interaction,
    user: typing.Optional[typing.Union[discord.User, discord.Member]] = None,
) -> None:
    """extract yours or other users' profile pictures"""

    await msg.response.defer()

    if user is None:
        user = msg.user

    await msg.followup.send(
        content="*no pfp found*" if user.avatar is None else user.avatar.url
    )


@cmds.new
async def servertime(
    msg: discord.interactions.Interaction,
    member: typing.Optional[discord.Member] = None,
) -> None:
    """shows how much time a person has stayed in this server"""

    await msg.response.defer()

    if member is None:
        member = msg.user  # type: ignore

    await msg.followup.send(
        content=f"{member.mention} has stayed here for \
**{humanize.precisedelta(datetime.timedelta(seconds=round(datetime.datetime.utcnow().timestamp() - member.joined_at.timestamp())), minimum_unit='seconds') if member.joined_at is not None else '[?]'}**"
    )


@cmds.new
async def neofetch(
    msg: discord.interactions.Interaction,
) -> None:
    """run neofetch"""

    await msg.response.defer()

    await msg.followup.send(
        content=f"""```
{const.ANSI_REGEX.sub("", check_output("neofetch").decode().strip().replace("`", "'"))[:1990]}
```"""
    )


@cmds.new
async def timelb(
    msg: discord.interactions.Interaction,
    local: bool = True,
) -> None:
    """server time leaderboard, if local is set to false it shows the global leadderboard"""

    stay_time: dict[str, float] = {}
    now: float = datetime.datetime.utcnow().timestamp()

    if local and msg.guild is not None:
        for m in msg.guild.members:
            if m.joined_at:
                stay_time[m.mention] = now - m.joined_at.timestamp()
    else:
        for g in cmds.b.guilds:
            for m in g.members:
                if m.joined_at:
                    stay_time[f"{m.mention} ( `{m.name}` ) in `{g.name}`"] = (
                        now - m.joined_at.timestamp()
                    )

    stay_time = {
        k: v
        for k, v in sorted(stay_time.items(), key=lambda item: item[1], reverse=True)
    }

    await menu.text_menu(
        msg,
        f"""{'local' if local else 'global'} stay time leaderboard

total users : {len(stay_time)}
average stay time : {humanize.precisedelta(datetime.timedelta(seconds=sum(stay_time.values()) / len(stay_time)), minimum_unit='seconds')}

"""
        + "\n".join(
            f"{idx}, {entry} for \
{humanize.precisedelta(datetime.timedelta(seconds=diff), minimum_unit='seconds')}"
            for idx, (entry, diff) in enumerate(stay_time.items(), 1)
        ),
    )


@cmds.new
async def music(
    msg: discord.interactions.Interaction,
) -> None:
    """play music in a voice chat"""

    await msg.response.defer()

    if msg.user.voice is None:  # type: ignore
        await msg.followup.send(content="join a voice chat babe xx")
        return

    c: typing.Optional[discord.VoiceProtocol] = None

    if msg.guild is None or (c := msg.guild.voice_client) is not None:
        await msg.followup.send(content=f"i am already connected to {'a voice channel' if c is None else c.channel.jump_url}")  # type: ignore
        return

    v: discord.VoiceClient = await msg.user.voice.channel.connect()  # type: ignore

    t: discord.Thread = await msg.channel.create_thread(  # type: ignore
        name=f"{msg.user.name}'s music control thread on {datetime.datetime.utcnow()} utc",
        type=discord.ChannelType.public_thread,  # type: ignore
    )

    await msg.followup.send(content=f"use {t.jump_url} to control the music and type `help` for help in that thread")  # type: ignore
    await music_mdl.Music(cmds.b, t, v).init()  # type: ignore


@cmds.new
async def tod(
    msg: discord.interactions.Interaction,
    type: TruthOrDare = TruthOrDare.random,
) -> None:
    """truth, dare or paranoia"""

    await msg.response.defer()

    true_type: TruthOrDare = type

    if true_type == TruthOrDare.random:
        true_type = RAND.choice(
            (
                TruthOrDare.truth,
                TruthOrDare.dare,
                TruthOrDare.paranoia,
            )
        )

    view: View = View(timeout=const.TOD_EXPIRES)
    btn: typing.Any = Button(
        style=discord.ButtonStyle.grey,
        label=f"another [{type.name}] ( expires in {humanize.precisedelta(datetime.timedelta(seconds=0 if view.timeout is None else view.timeout))} )",
    )

    async def cb(interaction: discord.interactions.Interaction) -> None:
        view.stop()
        await tod(msg=interaction, type=type)

    btn.callback = cb
    view.add_item(btn)

    end: str = "" if msg.user.discriminator == "0" else f"#{msg.user.discriminator}"

    await msg.followup.send(
        content=f"requested by {msg.user.mention} ( `{msg.user.name}{end}` )\n\n{true_type.name} : " + RAND.choice(true_type.value),  # type: ignore
        view=view,
        allowed_mentions=discord.mentions.AllowedMentions.none(),
    )


@cmds.new
async def src(
    msg: discord.interactions.Interaction,
) -> None:
    """show a link to the bots source code"""

    await msg.response.defer()
    await msg.followup.send(content=const.SOURCE)


@cmds.new
async def invite(
    msg: discord.interactions.Interaction,
) -> None:
    """link the top invite"""

    await msg.response.defer()

    invites: list[discord.Invite] = (
        []
        if msg.channel is None or msg.channel.guild is None
        else await msg.channel.guild.invites()
    )
    max_invites: typing.Optional[discord.Invite] = None

    for invite in invites:
        if max_invites is None or invite.uses > max_invites.uses:  # type: ignore
            max_invites = invite

    await msg.followup.send(
        content="no invites found"
        if max_invites is None
        else f"invite people using {max_invites.inviter.mention if max_invites.inviter is not None else 'server'}'s \
{max_invites.url} which has {max_invites.uses} uses",
        allowed_mentions=discord.AllowedMentions.none(),
    )


@cmds.new
async def cat(msg: discord.interactions.Interaction) -> None:
    """cat pic"""

    await msg.response.defer()
    await msg.followup.send(
        file=discord.File(
            BytesIO(requests.get("https://cataas.com/cat").content),
            filename="cat124.png",
        )
    )


@cmds.new
async def anime(msg: discord.interactions.Interaction) -> None:
    """anime pic"""

    await msg.response.defer()
    await msg.followup.send(
        file=discord.File(
            BytesIO(requests.get("https://pic.re/image").content),
            filename="anime124.png",
        ),
    )


@cmds.new
async def kicks(msg: discord.interactions.Interaction, user: typing.Optional[discord.user.User] = None) -> None:  # type: ignore
    """get your or other users' kick score"""

    if user is not None and user.bot:
        await menu.text_menu(msg, "bots cannot have kick scores")
        return

    score: typing.Any = (
        models.DB.query(models.ScoreKicks)  # type: ignore
        .where(models.ScoreKicks.author == (msg.user.id if user is None else user.id))  # type: ignore
        .first()
    )

    await menu.text_menu(
        msg,
        (("you have" if user is None else f"{user.mention} has") + " no kicks")
        if score is None
        else "the kick score for "
        + ("you" if user is None else user.mention)
        + f" is `{score.kicks}`",
    )


@cmds.new
async def kickslb(msg: discord.interactions.Interaction) -> None:  # type: ignore
    """get kick scores"""

    scores: typing.Any = models.DB.query(models.ScoreKicks).all()  # type: ignore

    if not scores:
        await menu.text_menu(msg, "no people currently have a kick score")
        return

    lb: dict[int, int] = dict(
        sorted(  # type: ignore
            {s.author: s.kicks for s in scores}.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )
    lbv: tuple[int] = tuple(lb.values())
    total_lbv: int = sum(lbv)

    await menu.text_menu(
        msg,
        "kick score leaderboard :\n\n"
        + "\n".join(
            f"{idx}, <@{value[0]}> with score `{value[1]}`"
            for idx, value in enumerate(lb.items(), 1)
        )
        + f"\n\naverage chat score : {total_lbv / len(lbv):.2f}\ntotal chat score : {total_lbv:.2f}",
    )
