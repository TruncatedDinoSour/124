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
    def _music_enum(self) -> typing.Generator[str, None, None]:
        for idx, item in enumerate(self.queue):
            if self.reset:
                return

            self.current = idx

            yield item

    async def _music(self) -> None:
        while self.run and self.voice.is_connected():
            self.reset = False

            for song in self._music_enum():  # type: ignore
                self.voice.play(
                    source := await YTDLSource.from_url(
                        song, self.ytdl, loop=self.b.loop  # type: ignore
                    )
                )

                await self.thread.send(
                    content=f"playing https://youtu.be/{source.data['id']}"[:2000]
                )

                while (
                    self.voice.is_connected()
                    and self.run
                    and self.current != -1
                    and not self.reset
                    and (self.voice.is_playing() or self.pause)
                ):
                    await asyncio.sleep(1)

                self.voice.stop()

            await asyncio.sleep(1)

    async def _cmds(self) -> None:
        mcmds.cmds.init(self)

        while self.run and self.voice.is_connected():
            while self.cqueue:
                await mcmds.cmds.push(self.cqueue.pop())

            await asyncio.sleep(1)

    def _play(self, url: str) -> None:
        info: dict[str, typing.Any] = self.ytdl.extract_info(url, download=False)  # type: ignore

        if "entries" not in info:
            self.queue.append(url)
        else:
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

        self.queue: list[str] = []
        self.cqueue: list[mcmdmgr.MusicCommand] = []
        self.ytdl: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(const.YTDL_OPTIONS)

        self.current: int = -1
        self.pause: bool = False
        self.reset: bool = False

        self.run: bool = True

        b.loop.create_task(self._music())
        b.loop.create_task(self._cmds())
        b.loop.create_task(self._quit())

    async def init(self) -> None:
        while self.run and self.voice.is_connected() and not self.thread.archived and not self.thread.locked and self.thread.member_count > 0:  # type: ignore
            try:
                m: discord.Message = await self.b.wait_for(  # type: ignore
                    "message", check=lambda m: m.channel == self.thread and m.content and not m.author.bot  # type: ignore
                )
            except asyncio.TimeoutError:
                continue

            m.content = m.content.strip()[: const.MUSIC_MAX_LEN].strip()

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

                Thread(target=self._play, args=(m.content,), daemon=True).start()
