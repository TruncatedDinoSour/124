#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot"""

import asyncio
import datetime
import random
import string
import typing

import discord
import discord.app_commands  # type: ignore
import humanize  # type: ignore
import sqlalchemy

from . import cmds, const, menu, models, util

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

    async def _kick_scores(self) -> typing.NoReturn:
        while True:
            await asyncio.sleep(const.SCORE_KICK_SLEEP)

            score_list: str = ""
            total_scores: int = 0

            score: models.Score

            for score in models.DB.query(models.Score):  # type: ignore
                if (
                    delta := round(
                        datetime.datetime.utcnow().timestamp() - score.last_act
                    )
                    + const.SCORE_KICK_ADD
                ) >= const.SCORE_KICK_DELTA:  # type: ignore
                    kick: models.ScoreKicks = (
                        models.DB.query(models.ScoreKicks).where(models.ScoreKicks.author == score.author).first()  # type: ignore
                    )

                    if kick is None:
                        models.DB.add(kick := models.ScoreKicks(author=score.author))

                    score_list += f"{total_scores + 1} ( kick #{kick.kicks + 1} ), <@{score.author}> no activity for \
{humanize.precisedelta(datetime.timedelta(seconds=delta), minimum_unit='seconds')} with score `{util.calc_score(score)}` ( {str(score)} )\n"
                    total_scores += 1

                    kick.kicks += 1
                    models.DB.session.execute(
                        sqlalchemy.delete(models.Score).where(
                            models.Score.author == score.author
                        )
                    )

            models.DB.commit()

            if total_scores > 0:
                score_list = f"kicked {total_scores} scores off the score leaderboard\n\n{score_list}"

                for g in self.guilds:
                    if (c := g.system_channel) is not None:
                        for page in await menu.wrap_text(score_list):
                            await c.send(content=page)
                            await asyncio.sleep(1)

                    await asyncio.sleep(1)

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
                            member.bot,
                        )
                    ):
                        util.get_score(member.id).vcs_joined += 1
                        self.vc_times.add(member.id)

        models.DB.commit()

        await self.ct.sync()

        self.loop.create_task(self._update_vc_score())
        self.loop.create_task(self._kick_scores())

    async def on_message(self, msg: discord.message.Message) -> None:
        if not msg.author.bot:
            util.update_act(msg.author.id)

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

        if msg.channel.name == const.OK_CHANNEL:  # type: ignore
            if msg.author.bot or msg.content != const.OK_CHANNEL:
                await msg.delete()
            else:
                util.get_score(msg.author.id).ok += 1
        elif msg.channel.name == const.RULES_CHANNEL:  # type: ignore
            if msg.author.bot:
                return

            msg.content = (
                " ".join(a.proxy_url for a in msg.attachments) + " " + msg.content
            )

            content: str = msg.content.strip()
            lcontent: str = content.lower()
            real: bool = any(lcontent.endswith(r) for r in const.REAL_RULES_ID)

            if not (real or any(lcontent.endswith(r) for r in const.FAKE_RULES_ID)):
                return

            for suf in const.REAL_RULES_ID if real else const.FAKE_RULES_ID:
                content = content.removesuffix(suf).strip()
                if content != msg.content:
                    break

            if not (content := content.strip()):
                return

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

        models.DB.commit()

    async def on_message_edit(
        self, _: discord.message.Message, msg: discord.message.Message
    ) -> None:
        await self.on_message(msg)

    async def on_member_join(self, member: discord.member.Member):
        if (c := member.guild.system_channel) is not None:
            end: str = "" if member.discriminator == "0" else f"#{member.discriminator}"

            await c.send(
                f"""welcome, {member.mention} ( `{member.name}{end}` ),

hope youre doing alright, you can check out @Clyde ( with an uppsercase C ) if \
you want to use clyde AI, you can also use {self.user.mention if self.user else 'my'} commands to use AI \
stuff : `/ai` and `/chatai`

also, dont forget to check out our rules using `/rules` command and \
make sure to show your respect to our national anthem -- WAP https://www.youtube.com/watch?v=Wc5IbN4xw70

also we have a system for chat score which you can check out using `/score` or `/scores`, \
although dont forget that this score is volatile, if youre not active for \
**{humanize.precisedelta(datetime.timedelta(seconds=const.SCORE_KICK_DELTA), minimum_unit='seconds')}** \
you will be kicked off the score leaderboard, every kick ull have a harder and harder time gaining score,
function `f(s) = s / K` where `K` is kick count and `s` is score

if you want to invite people use `/invite` command"""
            )

    async def on_member_remove(self, member: discord.member.Member):
        if (c := member.guild.system_channel) is not None:
            end: str = "" if member.discriminator == "0" else f"#{member.discriminator}"

            await c.send(
                f"""goodbye, {member.mention} ( `{member.name}{end}` ), \
thank you for being in this server for \
**{humanize.precisedelta(datetime.timedelta(seconds=round(datetime.datetime.utcnow().timestamp() - member.joined_at.timestamp())), minimum_unit='seconds') if member.joined_at is not None else "[?]"}**, \
keep in mind if you want to add people use `/invite` command

https://tenor.com/view/{'themercslaughing-gif-20727637' if random.randint(0, 1) else 'john-roblox-laugh-gif-22520624'}"""
            )

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if not member.bot:
            util.update_act(member.id)

        if (
            before.channel
            and before.channel.guild
            and before.channel.guild.voice_client
            and len(before.channel.members) == 1
        ):
            await before.channel.guild.voice_client.disconnect(force=True)

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
            and sum([(not u.bot) async for u in reaction.users()]) >= const.STAR_COUNT
            and reaction.message.guild
            and (
                channel_id := (
                    sb := util.get_starboard(reaction.message.guild.id)
                ).star_channel
            )
            and (channel := self.get_channel(channel_id)) is not None
            and f"{reaction.message.id}," not in sb.starred_msgs
        ):
            if not user.bot and not reaction.message.author.bot:
                util.get_score(reaction.message.author.id).starboard_score += 1

            sb.starred_msgs += f"{reaction.message.id},"
            models.DB.commit()

            mentions: discord.AllowedMentions = discord.AllowedMentions.none()
            mentions.users = (reaction.message.author,)

            msg: discord.Message = await channel.send(  # type: ignore
                f"{reaction.message.jump_url} • {reaction.message.author.mention} • >={const.STAR_COUNT} {const.STAR_EMOJI}\n\n\
{reaction.message.content[:const.STARBOARD_WRAP_LEN]}".strip(),
                files=[
                    await attachment.to_file()
                    for attachment in reaction.message.attachments
                ],
                allowed_mentions=mentions,
            )

            ref: typing.Optional[discord.MessageReference] = reaction.message.reference

            while ref is not None:
                refm: typing.Optional[  # type: ignore
                    discord.Message
                ] = await msg.channel.fetch_message(  # type: ignore
                    ref.message_id or 0  # type: ignore
                )

                if refm is None:
                    continue

                refmt: discord.AllowedMentions = discord.AllowedMentions.none()
                refmt.users = (refm.author.id,)  # type: ignore

                msg = await msg.reply(  # type: ignore
                    content=f"in reply to {refm.jump_url} by {refm.author.mention}\n\n{refm.content[:const.STARBOARD_WRAP_LEN].strip()}",  # type: ignore
                    files=[  # type: ignore
                        await attachment.to_file() for attachment in refm.attachments  # type: ignore
                    ],
                    allowed_mentions=mentions,
                )

                if not user.bot and not refm.author.bot:  # type: ignore
                    util.get_score(refm.author.id).stars_participated += 1  # type: ignore

                ref = refm.reference  # type: ignore

        if not user.bot:
            util.update_act(user.id)

        if (
            user.bot
            or reaction.message.author.bot
            or reaction.message.author.id == user.id
        ):
            return

        util.get_score(user.id).reactions_post += 1

        util.get_score(reaction.message.author.id).reactions_get += 1
        util.update_act(reaction.message.author.id)

        models.DB.commit()

    async def on_reaction_remove(
        self, reaction: discord.Reaction, user: discord.User
    ) -> None:
        if not user.bot:
            s: models.Score = util.get_score(user.id)

            if str(reaction.emoji) == const.STAR_EMOJI:
                s.stars_removed += 1

            util.update_act(user.id)

        if (
            user.bot
            or reaction.message.author.bot
            or reaction.message.author.id == user.id
        ):
            return

        s.reactions_post -= 1  # type: ignore
        util.get_score(reaction.message.author.id).reactions_get -= 1
        util.update_act(reaction.message.author.id)

        models.DB.commit()
