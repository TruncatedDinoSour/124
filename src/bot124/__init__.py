#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot"""

import typing
from datetime import datetime

import discord
import discord.app_commands  # type: ignore
import sqlalchemy

from . import const, menu, models

__all__: tuple[str] = ("Bot124",)


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
            sql_obj: typing.Any = (
                models.DB.session.query(models.Score)
                .where(models.Score.author == msg.author.id)
                .first()
            )

            if sql_obj is None:
                models.DB.add(sql_obj := models.Score(author=msg.author.id))

            sql_obj.total_messages += 1
            sql_obj.total_bytes += len(msg.content)

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

    @b.ct.command(name="rules", description="get all rules by filter")
    async def _(
        msg: discord.interactions.Interaction,
        id: typing.Optional[int] = None,
        real: typing.Optional[bool] = None,
        user: typing.Optional[discord.User] = None,
        yyyymmddhh_before: typing.Optional[str] = None,
        yyyymmddhh_after: typing.Optional[str] = None,
    ) -> None:  # type: ignore
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
            await msg.response.defer()
            await msg.followup.send(
                "invalid datetime format for yyyymmmddhh* arguments, keep in mind the format is yyyymmmddhh, so ***2023011023*** = 2023/01/10 23:00"
            )
            return

        rules: str = f"rules ( {q.count()} result( s ) ) :\n\n" if id is None else ""

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

        lb = {
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
        score: typing.Any = (
            models.DB.session.query(models.Score)
            .where(models.Score.author == (msg.user.id if user is None else user.id))  # type: ignore
            .first()
        )

        await menu.text_menu(
            msg,
            "no score found for this user"
            if score is None
            else f"the chat score for this user is `{score.total_bytes / score.total_messages * 100:.2f}` \
( `{score.total_bytes}` bytes thoughout `{score.total_messages}` messages )",
        )

    @b.ct.command(name="scores", description="get chat scores")
    async def _(msg: discord.interactions.Interaction) -> None:  # type: ignore
        scores: typing.Any = models.DB.session.query(models.Score).all()

        if not scores:
            await menu.text_menu(msg, "no people currently have a score")
            return

        lb: dict[int, int] = dict(
            sorted(
                {
                    s.author: s.total_bytes / s.total_messages * 100 for s in scores
                }.items(),
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
                f"{idx}, <@{value[0]}> with score {value[1]:.2f}"
                for idx, value in enumerate(lb.items(), 1)
            )
            + f"\n\naverage chat score : {total_lbv / len(lbv):.2f}\ntotal chat score : {total_lbv}",
        )
