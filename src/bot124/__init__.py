#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot"""

import asyncio
import string
import typing

import discord
import discord.app_commands  # type: ignore
import sqlalchemy

from . import cmds, const, models, util

__all__: tuple[str] = ("Bot124",)


class Bot124(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all())

        self.ct: discord.app_commands.CommandTree = discord.app_commands.CommandTree(
            self,
        )

        cmds.cmds.init(self.ct, self)

        self.vc_times: set[int] = set()

    async def _update_vc_score(self) -> typing.NoReturn:
        while True:
            await asyncio.sleep(1)

            for id in self.vc_times.copy():
                util.get_score(id).vcs_time += 1

            models.DB.commit()

    async def on_ready(self) -> None:
        models.DB.init()

        for guild in self.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    if member.voice and not any(
                        (
                            member.voice.mute,
                            member.voice.self_mute,
                            member.voice.deaf,
                            member.voice.self_deaf,
                        )
                    ):
                        util.get_score(member.id).vcs_joined += 1
                        self.vc_times.add(member.id)

        models.DB.commit()

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
                wc: typing.Optional[models.WordCloud] = (  # type: ignore
                    models.DB.query(models.WordCloud)  # type: ignore
                    .where(models.WordCloud.word == word)  # type: ignore
                    .first()
                )

                if wc is None:
                    models.DB.add(wc := models.WordCloud(word=word))
                    score.new_words += 1

                wc.usage += usage  # type: ignore

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
        if member.bot or member.voice is None:
            self.vc_times.discard(member.id)
            return

        score: models.Score = util.get_score(member.id)
        not_muted: bool = not (
            member.voice.mute
            or member.voice.self_mute
            or member.voice.deaf
            or member.voice.self_deaf
        )

        if before.channel is None and after.channel is not None:
            score.vcs_joined += 1
        elif before.channel is not None and after.channel is None:
            self.vc_times.discard(member.id)

        if not_muted:
            self.vc_times.add(member.id)
        else:
            self.vc_times.discard(member.id)

        models.DB.commit()

    async def on_reaction_add(
        self, reaction: discord.Reaction, user: discord.User
    ) -> None:
        if (
            str(reaction.emoji) == const.STAR_EMOJI
            and reaction.count >= const.STAR_COUNT
            and reaction.message.guild
            and (
                channel_id := (
                    sb := util.get_starboard(reaction.message.guild.id)
                ).star_channel
            )
            and (channel := self.get_channel(channel_id)) is not None
            and f"{reaction.message.id}," not in sb.starred_msgs
        ):
            sb.starred_msgs += f"{reaction.message.id},"
            models.DB.commit()
            await channel.send(
                f"{reaction.message.jump_url} • {reaction.message.author.mention} • >={const.STAR_COUNT} {const.STAR_EMOJI}\n\n{reaction.message.content[:const.MESSAGE_WRAP_LEN]}"
            )

        if (
            user.bot
            or reaction.message.author.bot
            or reaction.message.author.id == user.id
        ):
            return

        util.get_score(user.id).reactions_post += 1
        util.get_score(reaction.message.author.id).reactions_get += 1
        models.DB.commit()

    async def on_reaction_remove(
        self, reaction: discord.Reaction, user: discord.User
    ) -> None:
        if (
            user.bot
            or reaction.message.author.bot
            or reaction.message.author.id == user.id
        ):
            return

        util.get_score(user.id).reactions_post -= 1
        util.get_score(reaction.message.author.id).reactions_get -= 1
        models.DB.commit()
