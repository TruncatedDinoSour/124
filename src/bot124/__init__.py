#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot"""

import asyncio
import string
import typing

import discord
import discord.app_commands  # type: ignore
import sqlalchemy

from . import const, models, util, cmds

__all__: tuple[str] = ("Bot124",)


class Bot124(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all())

        self.ct: discord.app_commands.CommandTree = discord.app_commands.CommandTree(
            self,
        )

        cmds.cmds.init(self.ct, self)

        self.vc_times: list[int] = []

    async def _update_vc_score(self) -> typing.NoReturn:
        while True:
            await asyncio.sleep(1)

            for id in self.vc_times.copy():
                util.get_score(id).vcs_time += 1

            models.DB.commit()

    async def on_ready(self) -> None:
        models.DB.init()
        await self.ct.sync()
        self.loop.create_task(self._update_vc_score())

    async def on_message(self, msg: discord.message.Message) -> None:
        if msg.content and not msg.author.bot:
            # record scores

            score: models.Score = util.get_score(msg.author.id)
            score.total_messages += 1
            score.total_bytes += len(msg.content)

            # record wordcloud

            for word, usage in util.word_count(
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

        if isinstance(msg.channel, discord.channel.DMChannel):
            return

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

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        score: models.Score = util.get_score(member.id)

        if before.channel is None and after.channel is not None:
            self.vc_times.append(member.id)
            score.vcs_joined += 1
        elif before.channel is not None and after.channel is None:
            self.vc_times.remove(member.id)

        models.DB.commit()
