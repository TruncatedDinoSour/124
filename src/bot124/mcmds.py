#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""music commands"""

import textwrap
import typing
from secrets import SystemRandom
from threading import Thread

import discord
from freeGPT import gpt3

from . import const, mcmdmgr

cmds: mcmdmgr.MusicCommands = mcmdmgr.MusicCommands()

RAND: SystemRandom = SystemRandom()


@cmds.new
async def quit(music: typing.Any, *_) -> None:
    """makes the bot quit playing music"""

    await music.voice.disconnect()
    await music.thread.delete()
    music.run = False


@cmds.new
async def clear(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """clears the command and music queues"""

    music.queue.clear()
    music.cqueue.clear()
    music.reset = True
    await cmd.msg.reply(content="queue cleared")


@cmds.new
async def queue(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """lists the current queue"""

    for page in textwrap.wrap(
        f"music queue for `{music.thread.name}`\n\n"
        + (
            "".join(
                f"{'**[CURRENT]** ' if idx == (music.current + 1) else ''}{idx}, `{q}`\n"
                for idx, q in enumerate(music.queue, 1)
            )
            or "*none*"
        ),
        const.MESSAGE_WRAP_LEN,
        replace_whitespace=False,
    ):
        await cmd.msg.reply(
            content=page,
            allowed_mentions=discord.mentions.AllowedMentions.none(),
        )


@cmds.new
async def stop(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """pauses the audio playback of the bot"""

    if not music.pause:
        music.voice.pause()
        music.pause = True

    await cmd.msg.reply(content="paused audio playback")


@cmds.new
async def play(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """resume the audio playback"""

    if music.pause:
        music.voice.resume()
        music.pause = False

    await cmd.msg.reply(content="resumed audio playback")


@cmds.new
async def skip(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """skip current track which is playing"""

    music.current = -1
    await cmd.msg.reply(content="skipped this track")


@cmds.new
async def volume(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """set the volume, requires an argument `volume` which is the volume in percent, like volume 69.1 = 69.1%"""

    if music.voice.source is None:
        await cmd.msg.reply(content="i am currently not playing anything")
        return

    try:
        vol: float = float(cmd.args)
    except ValueError:
        await cmd.msg.reply(
            content=f"`{cmd.args}` is not a valid floating point integer"
        )
        return

    if vol < 0 or vol > 100:
        await cmd.msg.reply(content="this is not a valid volume")
        return

    music.voice.source.volume = vol / 100  # type: ignore

    await cmd.msg.reply(
        content=f"volume set to {vol}% ( {music.voice.source.volume} )"  # type: ignore
    )


@cmds.new
async def shuffle(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """shuffle the current queue"""

    RAND.shuffle(music.queue)
    music.reset = True
    await cmd.msg.reply(content="shuffled the queue")


@cmds.new
async def current(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """display the current playing track"""

    await cmd.msg.reply(
        content=f"currently playing {'nothing' if music.current == -1 else music.queue[music.current]}"
        + (
            ""
            if music.voice.source is None
            else f" audio : ||{music.voice.source.data['url']}||"
        )
    )


@cmds.new
async def pop(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """pops / removes last item off the queue"""

    await cmd.msg.reply(
        content=f"popped {music.queue.pop() if music.queue else 'nothing'} off the queue"
    )


@cmds.new
async def reset(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """plays the queue from index 0"""

    music.reset = True
    await cmd.msg.reply(content="queue reset")


@cmds.new
async def random(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """add random song ( ai generated )"""

    song: str = ""

    for _ in range(3):
        song = await gpt3.Completion.create(  # type: ignore
            "give me a random song that many people would like, just the title and the artist, no extra formatting or \
information, in a format 'artist - song'",  # type: ignore
        ).strip()  # type: ignore

        if song:
            break

    if song:
        await cmd.msg.reply(
            content=f"adding an ai generated song, `{song}` to the queue"
        )

        Thread(target=music._play, args=(song,), daemon=True).start()
