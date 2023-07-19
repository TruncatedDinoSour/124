#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""music commands"""

import textwrap
import typing
from secrets import SystemRandom

import discord

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
        content=f"currently playing `{'nothing' if music.current == -1 else music.queue[music.current]}`"
        + ("" if music.voice.source is None else f" audio : ||{music.voice.source.data['url']}||")
    )