#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""music manager"""

import asyncio
import string
import typing
from secrets import SystemRandom
from threading import Thread

import discord
import yt_dlp  # type: ignore

from . import const, mcmdmgr, mcmds

RAND: SystemRandom = SystemRandom()


class YTDLSource(discord.PCMVolumeTransformer):  # type: ignore
    def __init__(
        self,
        source: discord.AudioSource,
        *,
        data: dict[typing.Any, typing.Any],
        volume: float = 0.5,
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
        stream: bool = True,
    ) -> typing.Any:
        loop = loop or asyncio.get_event_loop()

        data: typing.Any = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)  # type: ignore
        )

        if "entries" in data:  # type: ignore
            data: typing.Any = data["entries"][0]

        return cls(discord.FFmpegPCMAudio(data["url"] if stream else ytdl.prepare_filename(data), **const.FFMPEG_OPTIONS), data=data)  # type: ignore


class Music:
    def _music_enum(self) -> typing.Generator[str, None, None]:
        for idx, item in enumerate(self.queue):
            if self.reset:
                return

            self.current = idx

            yield item

    async def _music(self) -> None:
        while self.voice.is_connected():
            self.reset = False

            for song in self._music_enum():  # type: ignore
                self.voice.play(
                    source := await YTDLSource.from_url(
                        song, self.ytdl, loop=self.b.loop  # type: ignore
                    )
                )

                await self.thread.send(
                    content=f"playing https://youtu.be/{source.data['id']} from `{song}`"[
                        :2000
                    ]
                )

                while (
                    self.voice.is_connected()
                    and self.current != -1
                    and not self.reset
                    and (self.voice.is_playing() or self.pause)
                ):
                    await asyncio.sleep(1)

                self.voice.stop()

            await asyncio.sleep(1)

    async def _cmds(self) -> None:
        mcmds.cmds.init(self)

        while mcmds.cmds.run and self.voice.is_connected():
            while self.cqueue:
                await mcmds.cmds.push(self.cqueue.pop())

            await asyncio.sleep(1)

    def _playlist_thread(self, url: str) -> None:
        info: dict[str, typing.Any] = self.ytdl.extract_info(url, download=False)  # type: ignore

        if "entries" not in info:
            self.queue.append(url)
        else:
            for entry in info["entries"]:
                if entry:
                    self.queue.append(f"https://youtu.be/{entry['id']}")

    def __init__(
        self,
        b: discord.Client,
        thread: discord.Thread,
        voice: discord.VoiceClient,
    ) -> None:
        self.b: discord.Client = b
        self.thread: discord.Thread = thread
        self.voice: discord.VoiceClient = voice

        self.queue: list[str] = []
        self.cqueue: list[mcmdmgr.MusicCommand] = []
        self.ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(const.YTDL_OPTIONS)

        self.current: int = -1
        self.pause: bool = False
        self.reset: bool = False

        b.loop.create_task(self._music())
        b.loop.create_task(self._cmds())

    async def init(self) -> None:
        while self.voice.is_connected() and not self.thread.archived and not self.thread.locked and self.thread.member_count > 0:  # type: ignore
            try:
                m: discord.Message = await self.b.wait_for(  # type: ignore
                    "message", check=lambda m: m.channel == self.thread and m.content and not m.author.bot  # type: ignore
                )
            except asyncio.TimeoutError:
                continue

            try:
                cmd, args = (
                    m.content.split(maxsplit=1)
                    + [
                        "",
                    ]
                )[:2]
                cmd = cmd.lower()

                self.cqueue.append(
                    mcmdmgr.MusicCommand(args, mcmdmgr.MusicCommandT(cmd), m)
                )
            except ValueError:
                await m.reply(content=f"adding `{m.content}` to the queue")

                if (
                    any(c in string.whitespace for c in m.content)
                    or "/" not in m.content
                ):
                    self.queue.append(m.content)
                else:
                    Thread(
                        target=self._playlist_thread, args=(m.content,), daemon=True
                    ).start()
