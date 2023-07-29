#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""music manager"""

import asyncio
import typing
from secrets import SystemRandom
from threading import Thread

import discord
import validators  # type: ignore
import yt_dlp  # type: ignore

from . import const, mcmdmgr, mcmds

RAND: SystemRandom = SystemRandom()


class YTDLSource(discord.PCMVolumeTransformer):  # type: ignore
    def __init__(
        self,
        source: discord.AudioSource,
        *,
        data: dict[typing.Any, typing.Any],
        volume: float = const.MUSIC_DEFAULT_VOL,
    ) -> None:
        super().__init__(source, volume)  # type: ignore
        self.data: dict[typing.Any, typing.Any] = data

    @classmethod
    async def from_url(
        cls,
        url: str,
        ytdl: yt_dlp.YoutubeDL,
        *,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> typing.Any:
        loop = loop or asyncio.get_event_loop()

        data: typing.Any = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False)  # type: ignore
        )

        if data is None:
            return

        if "entries" in data:  # type: ignore
            data: typing.Any = data["entries"][0]

        return cls(discord.FFmpegPCMAudio(data["url"], **const.FFMPEG_OPTIONS), data=data)  # type: ignore


class Music:
    async def _music(self) -> None:
        while self.run and self.voice.is_connected():
            if self.current < 0:
                self.current = 0

            while self.queue:
                previous_current: int = self.current

                self.voice.play(
                    await YTDLSource.from_url(
                        url := self.queue[self.current], self.ytdl, loop=self.b.loop  # type: ignore
                    )
                )

                await self.thread.send(
                    content=f"[{previous_current + 1}/{len(self.queue)}] playing {url}"
                )

                while (
                    self.voice.is_connected()
                    and self.run
                    and self.current == previous_current
                    and (self.voice.is_playing() or self.voice.is_paused())
                ):
                    await asyncio.sleep(1)

                self.voice.stop()

                if not self.repeat and self.current == previous_current:
                    if self.current + 1 < len(self.queue):
                        self.current += 1
                    elif self.loop:
                        self.current = 0

                break

            await asyncio.sleep(1)

    async def _cmds(self) -> None:
        mcmds.cmds.init(self)

        while self.run and self.voice.is_connected():
            while self.cqueue:
                await mcmds.cmds.push(self.cqueue.pop(0))

            await asyncio.sleep(1)

    def _play(self, url: str) -> None:
        info: typing.Optional[dict[str, typing.Any]] = self.ytdl.extract_info(url, download=False)  # type: ignore

        if info is None:
            return

        if "entries" not in info:
            self.queue.append(url)
        else:
            if not info["entries"]:
                return

            if not validators.url(url):  # type: ignore
                self.queue.append(f"https://youtu.be/{info['entries'][0]['id']}")
            else:
                for entry in info["entries"]:  # type: ignore
                    if entry:
                        self.queue.append(f"https://youtu.be/{entry['id']}")

    async def _quit(self) -> None:
        while self.run and self.voice.is_connected():
            await asyncio.sleep(1)

        await mcmds.quit(self, None)  # type: ignore

    def __init__(
        self,
        b: discord.Client,
        thread: discord.Thread,
        voice: discord.VoiceClient,
    ) -> None:
        self.b: discord.Client = b
        self.thread: discord.Thread = thread
        self.voice: discord.VoiceClient = voice

        self.ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(const.YTDL_OPTIONS)

        self.queue: list[str] = []
        self.cqueue: list[mcmdmgr.MusicCommand] = []

        self.current: int = 0

        self.run: bool = True

        self.loop: bool = False
        self.repeat: bool = False

        b.loop.create_task(self._music())
        b.loop.create_task(self._cmds())
        b.loop.create_task(self._quit())

    async def init(self) -> None:
        mentions: discord.AllowedMentions = discord.AllowedMentions.none()
        mentions.replied_user = True

        while self.run and self.voice.is_connected() and not self.thread.archived and not self.thread.locked and self.thread.member_count > 0:  # type: ignore
            try:
                m: discord.Message = await self.b.wait_for(  # type: ignore
                    "message",
                    check=lambda m: m.channel == self.thread
                    and m.content
                    and not m.author.bot
                    and not m.content.startswith(const.MUSIC_COMMENT),  # type: ignore
                )
            except asyncio.TimeoutError:
                continue

            m.content = m.content.strip()[: const.MUSIC_MAX_LEN].strip()

            if not m.content:
                continue

            cmd, args = (
                m.content.split(maxsplit=1)
                + [
                    "",
                ]
            )[:2]
            cmd = cmd.lower()

            if cmd in mcmds.cmds.cmds:
                self.cqueue.append(mcmdmgr.MusicCommand(args, cmd, m))
            else:
                await m.reply(
                    content=f"adding `{m.content}` ( #{len(self.queue) + 1} ) to the queue",
                    allowed_mentions=mentions,
                )
                Thread(target=self._play, args=(m.content,), daemon=True).start()
