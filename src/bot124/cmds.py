#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bot 124 commands"""

import asyncio
import datetime
import json
import typing
from enum import Enum, auto
from http import HTTPStatus
from io import BytesIO
from secrets import SystemRandom
from subprocess import check_output

import aiohttp
import discord
import discord.app_commands  # type: ignore
import humanize  # type: ignore
import sqlalchemy
import uwuify  # type: ignore
import yt_dlp  # type: ignore
from discord.ui import Button, View
from rebelai import enums as ai_enums
from rebelai.ai.deepai import deepai as deepai_ai
from rebelai.ai.prodia import prodia as prodia_ai
from rule34Py import rule34Py as Rule34  # type: ignore

from . import ai as ai_impl
from . import const, menu, models
from . import music as music_mdl
from . import util
from .cmdmgr import CommandManager

__all__: tuple[str] = ("cmds",)

cmds: CommandManager = CommandManager()
RAND: SystemRandom = SystemRandom()

_PRODIA_MODELS: tuple[str, ...] = tuple(
    map(lambda item: item.name, ai_enums.ProdiaModel)
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

    await menu.text_menu(msg, rules or "*no rules found*")


@cmds.new
async def ruleslb(
    msg: discord.interactions.Interaction,
    local: bool = False,
) -> None:  # type: ignore
    """rules leaderboard by rule creation count"""

    lb: typing.Dict[int, int] = {}

    members: tuple[int] = tuple()

    if local:
        members = (
            tuple(map(lambda m: m.id, msg.guild.members)) if msg.guild else members
        )

    for (author,) in models.DB.query(sqlalchemy.distinct(models.Rule.author)).all():  # type: ignore
        if local and author not in members:
            continue

        lb[author] = (  # type: ignore
            models.DB.query(sqlalchemy.distinct(models.Rule.id))  # type: ignore
            .where(models.Rule.author == author)
            .count()
        )

    if not lb:
        await menu.text_menu(msg, "no rules found")
        return

    lb: dict[int, int] = {
        k: v for k, v in sorted(lb.items(), key=lambda item: item[1], reverse=True)
    }
    total: int = sum(lb.values())

    await menu.text_menu(
        msg,
        f"rules leaderboard\n\n{total} rule( s ) in total\n\n"
        + "".join(
            f"{rank}, <@{id}> with {count} ( {(count / total * 100):.2f}% ) created rule( s )\n"
            for rank, (id, count) in enumerate(lb.items(), 1)
        ),
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
async def scorelb(
    msg: discord.interactions.Interaction,
    local: bool = False,
) -> None:  # type: ignore
    """get chat scores"""

    scores: typing.Any = models.DB.query(models.Score).all()  # type: ignore

    if local:
        members: tuple[int, ...] = (
            tuple(map(lambda m: m.id, msg.guild.members)) if msg.guild else tuple()
        )
        scores = tuple(score for score in scores if score.author in members)

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
        f"""chat score leaderboard

average chat score : {total_lbv / len(lbv):.2f}
total chat score : {total_lbv:.2f}

"""
        + "\n".join(
            f"{idx}, <@{value[0]}> with score `{value[1]}`"
            for idx, value in enumerate(lb.items(), 1)
        ),
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


@cmds.nnew
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
    model: ai_impl.TextAI = ai_impl.TextAI.gpt3,
) -> None:
    """generate content using an AI large language model"""

    await msg.followup.send(
        content=(
            await ai_impl.gen_ai_text(
                prompt,
                model,
                False,
            )
        )
        or "*no content*",  # type: ignore
    )


@cmds.new
async def aiimg(
    msg: discord.interactions.Interaction,
    prompt: str,
    model: ai_impl.ImageAI = ai_impl.ImageAI.pollinations,
) -> None:
    """generate content using an AI image model"""

    await msg.followup.send(file=await ai_impl.gen_ai_img(prompt, model))


@cmds.new
async def chatai(
    msg: discord.interactions.Interaction,
    model: ai_impl.TextAI = ai_impl.TextAI.gpt3,
) -> None:
    """create a thread with an AI model"""

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
            r = await ai_impl.gen_ai_text(chat, model)

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

    guilds: str = ""

    if not local:
        guilds = f"""
guilds : {len(cmds.b.guilds)} ( `{"`, `".join(g.name for g in cmds.b.guilds)}` )
average member count : {len(stay_time) / len(cmds.b.guilds):.2f}"""

    await menu.text_menu(
        msg,
        f"""{'local' if local else 'global'} stay time leaderboard

total users : {len(stay_time)}{guilds}
average stay time : {humanize.precisedelta(datetime.timedelta(seconds=round(sum(stay_time.values()) / len(stay_time), 2)), minimum_unit='seconds')}

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
        await tod(interaction, type=type)

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

    await msg.followup.send(content=const.SOURCE)


@cmds.new
async def invite(
    msg: discord.interactions.Interaction,
) -> None:
    """link the top invite"""

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
async def cat(
    msg: discord.interactions.Interaction,
    gif: bool = False,
    says: typing.Optional[str] = None,
    tag: typing.Optional[str] = None,
    http: typing.Optional[int] = None,
) -> None:
    """cat pic"""

    if http is not None:
        await msg.followup.send(
            content=f"https://http.cat/{http}.jpg"
            if http in tuple(HTTPStatus.__members__.values()) + (420,)
            else "not a valid http code"
        )
        return

    if tag is not None:
        tag = tag.lower()

        if tag not in const.CAT_TAGS:
            await menu.text_menu(
                msg,
                f"invalid tag `{tag}`, list of available tags :\n\n"
                + "".join(f"{idx}, {t}\n" for idx, t in enumerate(const.CAT_TAGS, 1)),
                wrap=const.WORDCLOUD_WRAP,
            )
            return

    gif = gif and not any((says, tag))

    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"https://cataas.com/cat{('/' + tag) if tag else ''}{('/says/' + says) if says else ''}{'/gif' if gif else ''}"
        ) as r:
            await msg.followup.send(
                file=discord.File(
                    BytesIO(await r.content.read()),
                    filename=f"cat124.{'gif' if gif else 'png'}",
                )
            )


@cmds.new
async def anime(
    msg: discord.interactions.Interaction,
    lang: typing.Optional[str] = None,
) -> None:
    """anime girls holding programming books pics"""

    if lang is not None and lang not in const.ANIME_DIRS:
        await menu.text_menu(
            msg,
            f"invalid lang `{lang}`, list of available langs :\n\n"
            + "".join(f"{idx}, {t}\n" for idx, t in enumerate(const.ANIME_DIRS, 1)),
            wrap=const.WORDCLOUD_WRAP,
        )
        return

    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{const.ANIME_GITHUB_API}/{RAND.choice(const.ANIME_DIRS) if lang is None else lang}"
        ) as r:
            await msg.followup.send(content=RAND.choice(await r.json())["download_url"])


@cmds.new
async def kicks(
    msg: discord.interactions.Interaction,
    user: typing.Optional[discord.user.User] = None,
) -> None:
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
async def kickslb(msg: discord.interactions.Interaction) -> None:
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
        f"""kick score leaderboard

average kick score : {total_lbv / len(lbv):.2f}
total kick score : {total_lbv:.2f}

        """
        + "\n".join(
            f"{idx}, <@{value[0]}> with score `{value[1]}`"
            for idx, value in enumerate(lb.items(), 1)
        ),
    )


@cmds.new
async def advice(
    msg: discord.interactions.Interaction, query: typing.Optional[str] = None
) -> None:
    """get or search for advice"""

    s: aiohttp.ClientSession = aiohttp.ClientSession()

    if query is not None:
        await menu.text_menu(
            msg,
            "\n".join(
                f"{idx}, advice #{advice['id']} @ {advice['date']} : {advice['advice']}"
                for idx, advice in enumerate(  # type: ignore
                    json.loads(
                        await (await s.get(f"{const.ADVICE_API}/search/{query}")).text()  # type: ignore
                    ).get("slips")
                    or [],
                    1,
                )
            )
            or "*no advice found :(*",
        )
    else:
        advice: dict[str, typing.Union[int, str]] = json.loads(
            await (await s.get(const.ADVICE_API)).text()
        )["slip"]
        await menu.text_menu(msg, f"advice #{advice['id']} : {advice['advice']}")

    await s.close()


@cmds.new
async def tr(
    msg: discord.interactions.Interaction,
    text: str,
    to_lang: str,
    from_lang: str = const.DEFAULT_TRANSLATE_SOURCE,
) -> None:
    """translate from one language to another using deepL ai"""

    await menu.menu(
        msg,
        await ai_impl.translate(
            text=text,
            to_lang=to_lang.upper(),
            from_lang=from_lang.upper(),
        ),
    )


@cmds.new
async def deepai(
    msg: discord.interactions.Interaction,
    model: typing.Optional[ai_enums.DeepAIModel] = None,
    text: typing.Optional[str] = None,
    image: typing.Optional[discord.Attachment] = None,
    image1: typing.Optional[discord.Attachment] = None,
    image2: typing.Optional[discord.Attachment] = None,
) -> None:
    """interract with all deepai models, run with no arguments for more info abt arguments"""

    if model is None or all(arg is None for arg in (text, image, image1, image2)):
        await msg.followup.send(
            content="""- `model` is required

text :
- text2img
- text-generator
- fantasy-world-generator
- stable-diffusion
- cyberpunk-generator
- cute-creature-generator
- renaissance-painting-generator
- old-style-generator
- anime-portrait-generator
- surreal-graphics-generator
- 3d-objects-generator
- impressionism-painting-generator
- watercolor-painting-generator
- 3d-character-generator
- future-architecture-generator
- anime-world-generator
- steampunk-generator
- street-art-generator
- origami-3d-generator
- hologram-3d-generator

image + text :
- image-editor

image :
- torch-srgan
- waifu2x
- nsfw-detector

image1 + image2 :
- image-similarity"""
        )
        return

    async def read(f: typing.Optional[discord.Attachment]) -> bytes:
        return (await f.read()) if f is not None else b""

    out: dict[str, typing.Any] = await deepai_ai(
        model=model,
        data={
            "text": text or "",
            "image": await read(image),
            "image1": await read(image1),
            "image2": await read(image2),
        },
    )

    realout: str = ""

    for r in "output", "output_url", "err":
        if r in out:
            realout += f"{r} : {out[r]}\n\n"

    await msg.followup.send(
        content=realout.strip()
        or f"""```json
{json.dumps(out, indent=4)}
```""",
    )


@cmds.new
async def prodia(
    msg: discord.interactions.Interaction,
    prompt: str,
    model: typing.Literal[*_PRODIA_MODELS[:25]] = ai_enums.ProdiaModel.REALISTIC_VISION_V5_0.name,  # type: ignore
    model1: typing.Optional[typing.Literal[*_PRODIA_MODELS[25:]]] = None,  # type: ignore
    sampler: ai_enums.ProdiaSampler = ai_enums.ProdiaSampler.EULER,
    seed: int = -1,
    negative: bool = True,
) -> None:
    """prodia image generation ( with more options )"""

    model = model1 or model  # type: ignore

    await msg.followup.send(
        file=discord.File(
            fp=BytesIO(
                await prodia_ai(
                    prompt=prompt,
                    model=getattr(ai_enums.ProdiaModel, model),  # type: ignore
                    sampler=sampler,
                    seed=seed,
                    negative=negative,
                )
            ),
            filename=f"124_prodia_{model}_{sampler.name}_{seed}_{'neg' if negative else 'nneg'}_generation_{datetime.datetime.utcnow()}.png",
        ),
    )


@cmds.new
async def everyone(
    msg: discord.interactions.Interaction,
    content: str,
) -> None:
    """ping everyone individually instead of `@everyone`"""

    if not msg.user.guild_permissions.mention_everyone:  # type: ignore
        await msg.followup.send(content="u have no `everyone ping` permission")
        return

    if msg.guild is None:
        await msg.followup.send(content="no guild / message in the interraction ( ? )")
        return

    message: discord.WebhookMessage = await msg.followup.send(content=content)  # type: ignore

    for page in menu.wrap_text(
        " ".join("" if member.bot else member.mention for member in msg.guild.members)
    ):
        await message.reply(content=page)


@cmds.new
async def yt(
    msg: discord.interactions.Interaction,
    query: str,
) -> None:
    """search stuff on youtube"""

    ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(const.YTDL_OPTIONS)
    data: typing.Any = await asyncio.get_event_loop().run_in_executor(
        None, lambda: ytdl.extract_info(query, download=False)  # type: ignore
    )

    if data is None:
        await msg.followup.send(content="*no results*")
        return

    if "entries" in data:
        data: typing.Any = data["entries"][0]

    await msg.followup.send(content=f"https://youtu.be/{data['id']}")


@cmds.new
async def r34(
    msg: discord.interactions.Interaction,
    tags: str,
) -> None:
    """rule 34 :( ( add multiple tags using `:` or `;` )"""

    await menu.menu(
        msg,
        tuple(
            s.sample  # type: ignore
            for s in Rule34().search(  # type: ignore
                tags.lower().replace(" ", "_").replace(";", ":").split(":"),
            )
        )
        or ("*no results*",),
    )


@cmds.new
async def guilds(
    msg: discord.interactions.Interaction,
) -> None:
    """what servers 124 is used in"""

    await menu.text_menu(
        msg,
        "\n".join(
            f"{idx}, `{guild.name}`" for idx, guild in enumerate(cmds.b.guilds, 1)
        ),
    )


@cmds.new
async def icon(
    msg: discord.interactions.Interaction,
) -> None:
    """server icon"""

    await menu.text_menu(
        msg,
        msg.guild.icon.url if msg.guild and msg.guild.icon else "*no server icon*",
    )


@cmds.new
async def uwu(
    msg: discord.interactions.Interaction,
    content: str,
) -> None:
    """uwuify t-text UwU"""

    await menu.text_menu(
        msg,
        uwuify.uwu(content, flags=uwuify.SMILEY | uwuify.YU),  # type: ignore
    )


@cmds.new
@cmds.admin
async def tkill(msg: discord.interactions.Interaction) -> None:
    """close all open threads"""

    for c in msg.guild.text_channels:  # type: ignore
        for t in c.threads:  # type: ignore
            await t.edit(archived=True)  # type: ignore

    await menu.text_menu(
        msg,
        "closed all open threads",
    )


@cmds.new
async def readme(msg: discord.interactions.Interaction) -> None:
    """read this"""

    await menu.text_menu(
        msg,
        "goodbye, 124, this bot is no longer supported, use https://ari-web.xyz/gh/124tg instead",
    )
