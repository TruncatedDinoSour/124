#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot"""

import math
import string
import typing
from datetime import datetime

import discord
import discord.app_commands  # type: ignore
import sqlalchemy

from . import const, menu, models

__all__: tuple[str] = ("Bot124",)


def word_count(lst: typing.Iterable[str]) -> dict[str, int]:
    word_dict: dict[str, int] = {}

    for word in lst:
        if word in word_dict:
            word_dict[word] += 1
        else:
            word_dict[word] = 1

    return word_dict


def filter_rules(
    id: typing.Optional[int] = None,
    real: typing.Optional[bool] = None,
    user: typing.Optional[discord.User] = None,
    yyyymmddhh_before: typing.Optional[str] = None,
    yyyymmddhh_after: typing.Optional[str] = None,
) -> typing.Any:  # type: ignore
    q: typing.Any = models.DB.session.query(models.Rule)

    if real is not None:
        q = q.filter(models.Rule.real == real)

    if user is not None:
        q = q.filter(models.Rule.author == user.id)

    if id is not None:
        q = q.filter(models.Rule.id == id)

    try:
        if yyyymmddhh_before is not None:
            q = q.filter(
                models.Rule.timestamp
                <= datetime.strptime(yyyymmddhh_before, "%Y%m%d%H").timestamp()
            )

        if yyyymmddhh_after is not None:
            q = q.filter(
                models.Rule.timestamp
                >= datetime.strptime(yyyymmddhh_after, "%Y%m%d%H").timestamp()
            )
    except ValueError:
        return "invalid datetime format for yyyymmmddhh* arguments, keep in mind the format is yyyymmmddhh, so ***2023011023*** = 2023/01/10 23:00"

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
                )
                / const.GOLDEN_RATIO
            )
            * math.pi
        )
        + (1 / 90),
        2,
    )


class Bot124(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all())

        self.ct: discord.app_commands.CommandTree = discord.app_commands.CommandTree(
            self,
        )

        load_cmds(self)

    async def on_ready(self) -> None:
        models.DB.init()
        await self.ct.sync()

    async def on_message(self, msg: discord.message.Message) -> None:
        if not msg.author.bot:
            # record scores

            sql_obj: typing.Any = (
                models.DB.session.query(models.Score)
                .where(models.Score.author == msg.author.id)
                .first()
            )

            if sql_obj is None:
                models.DB.add(sql_obj := models.Score(author=msg.author.id))

            sql_obj.total_messages += 1
            sql_obj.total_bytes += len(msg.content)

            # record wordcloud

            for word, usage in word_count(
                "".join(c for c in msg.content.lower() if c not in string.punctuation)
                .strip()
                .split()
            ).items():
                sql_obj = (
                    models.DB.session.query(models.WordCloud)
                    .where(models.WordCloud.word == word)
                    .first()
                )

                if sql_obj is None:
                    models.DB.add(sql_obj := models.WordCloud(word=word))

                sql_obj.usage += usage

            models.DB.commit()

        if msg.channel.name == const.OK_CHANNEL and (msg.author.bot or msg.content != const.OK_CHANNEL):  # type: ignore
            await msg.delete()
        elif msg.channel.name == const.RULES_CHANNEL:  # type: ignore
            if msg.author.bot:
                return

            content: str = msg.content.strip()
            lcontent: str = content.lower()
            real: bool = any(lcontent.endswith(r) for r in const.REAL_RULES_ID)

            if not (real or any(lcontent.endswith(r) for r in const.FAKE_RULES_ID)):
                return

            for suf in const.REAL_RULES_ID if real else const.FAKE_RULES_ID:
                content = content.removesuffix(suf).strip()
                if content != msg.content:
                    break

            try:
                models.DB.add(
                    rule := models.Rule(
                        content=content,
                        real=real,
                        author=msg.author.id,
                    )
                )

                await msg.reply(content=f"{'real' if real else 'fake'} rule #{rule.id}")
            except sqlalchemy.exc.IntegrityError:  # type: ignore
                await msg.delete()

    async def on_message_edit(
        self, _: discord.message.Message, msg: discord.message.Message
    ) -> None:
        await self.on_message(msg)

    async def on_member_join(self, member: discord.member.Member):
        if (c := member.guild.system_channel) is not None:
            await c.send(
                f"w-wewcome {member.mention} ( {member.name}#{member.discriminator} ), XD have fun w-with @Clyde ( uppewcase c ), \
>_< a-awso d-dont miss o-out on `/rules` :3"
            )

    async def on_member_remove(self, member: discord.member.Member):
        if (c := member.guild.system_channel) is not None:
            await c.send(
                f"goodbye {member.mention} ( {member.name}#{member.discriminator} ) ^w^, (U ᵕ U❁) h-haww a ny-nice day :3"
            )


def load_cmds(b: Bot124) -> None:
    @b.ct.command(name="status", description="set or reset bots 'playing' status")
    async def _(msg: discord.interactions.Interaction, value: typing.Union[str, None] = None) -> None:  # type: ignore
        await msg.response.defer()

        if value is not None:
            value = value[: const.MAX_PRESENCE_LEN].strip()

        await b.change_presence(
            activity=None if value is None else discord.Game(name=value)
        )

        await msg.followup.send(
            content="'playing' status has been reset"
            if value is None
            else f"status is now : `playing {value}`"
        )

    @b.ct.command(name="rules", description="get rules by filter and / or query")
    async def _(
        msg: discord.interactions.Interaction,
        query: typing.Optional[str] = None,
        id: typing.Optional[int] = None,
        real: typing.Optional[bool] = None,
        user: typing.Optional[discord.User] = None,
        yyyymmddhh_before: typing.Optional[str] = None,
        yyyymmddhh_after: typing.Optional[str] = None,
        limit: int = const.MIN_RULES_LIMIT,
    ) -> None:  # type: ignore
        q: typing.Any = filter_rules(
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
            f"rules ( {len(q)}/{models.DB.session.query(models.Rule.id).count()} result( s ) ) :\n\n"
            if id is None
            else ""
        )

        for r in q:
            rules += f"{r.id}, {r.content} ( {'real' if r.real else 'fake'} rule ) by <@{r.author}> on {str(datetime.utcfromtimestamp(r.timestamp))} UTC\n"

        await menu.text_menu(msg, rules)

    @b.ct.command(name="lb", description="rules leaderboard by rule creation count")
    async def _(msg: discord.interactions.Interaction) -> None:  # type: ignore
        lb: typing.Dict[int, int] = {}

        for (author,) in models.DB.session.query(
            sqlalchemy.distinct(models.Rule.author)
        ).all():
            lb[author] = (
                models.DB.session.query(sqlalchemy.distinct(models.Rule.id))
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

    @b.ct.command(
        name="score", description="get your or other users' chat score chat score"
    )
    async def _(msg: discord.interactions.Interaction, user: typing.Optional[discord.user.User] = None) -> None:  # type: ignore
        if user is not None and user.bot:
            await menu.text_menu(msg, "bots cannot have scores")
            return

        score: typing.Any = (
            models.DB.session.query(models.Score)
            .where(models.Score.author == (msg.user.id if user is None else user.id))  # type: ignore
            .first()
        )

        await menu.text_menu(
            msg,
            (("you have" if user is None else f"{user.mention} has") + " no score")
            if score is None
            else "the chat score for "
            + ("you" if user is None else user.mention)
            + f" is `{calc_score(score)}` \
( `{score.total_bytes}` bytes throughout `{score.total_messages}` messages )",
        )

    @b.ct.command(name="scores", description="get chat scores")
    async def _(msg: discord.interactions.Interaction) -> None:  # type: ignore
        scores: typing.Any = models.DB.session.query(models.Score).all()

        if not scores:
            await menu.text_menu(msg, "no people currently have a score")
            return

        lb: dict[int, int] = dict(
            sorted(
                {s.author: calc_score(s) for s in scores}.items(),
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

    @b.ct.command(
        name="wordcloud", description="get the word cloud by filter, limit and query"
    )
    async def _(
        msg: discord.interactions.Interaction,
        limit: int = const.MIN_WORDCLOUD_LIMIT,
        usage_lt: typing.Optional[int] = None,
        usage_mt: typing.Optional[int] = None,
        query: typing.Optional[str] = None,
    ) -> None:  # type: ignore
        q: typing.Any = models.DB.session.query(models.WordCloud).order_by(
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
            f"word cloud ( {ql}/{models.DB.session.query(models.WordCloud.usage).count()} word( s ) )\n\n"
            + (
                "".join(
                    f"{idx}, {w.word} ( {w.usage} ( {w.usage / ql * 100:.2f}% ) )\n"
                    for idx, w in enumerate(q, 1)
                )
            ),
            const.WORDCLOUD_WRAP,
        )
