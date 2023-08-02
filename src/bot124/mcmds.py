#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""music commands"""

import asyncio
import textwrap
import typing
from secrets import SystemRandom
from threading import Thread

from freeGPT import gpt3  # type: ignore

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
    music.current = -1

    await cmd.msg.reply(content="queue cleared")


@cmds.new
async def queue(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """lists the current queue"""

    for page in textwrap.wrap(
        f"music queue for {music.thread.jump_url}\n\n"
        + "".join(
            f"{'**[CURRENT]** ' if idx == (music.current + 1) else ''}{idx}, <{q}>\n"
            for idx, q in enumerate(music.queue, 1)
        ),
        const.MESSAGE_WRAP_LEN,
        replace_whitespace=False,
    ):
        await cmd.msg.reply(content=page)


@cmds.new
async def pause(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """pauses the audio playback of the bot"""

    music.voice.pause()
    await cmd.msg.reply(content="paused audio playback")


@cmds.new
async def play(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """resume the audio playback"""

    music.voice.resume()
    await cmd.msg.reply(content="resumed audio playback")


@cmds.new
async def next(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """skip / next current track, which is playing, loops"""

    music.current = (music.current + 1) if music.current + 1 < len(music.queue) else 0
    await cmd.msg.reply(content="skipped this track")


@cmds.new
async def begin(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """skip to the beginning of the queue"""

    music.current = -1
    await cmd.msg.reply(content="skipped to beginning")


@cmds.new
async def end(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """skip to the end of the queue"""

    music.current = len(music.queue) - 1
    await cmd.msg.reply(content="skipped to end")


@cmds.new
async def back(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """go back a track, loops"""

    music.current = (
        (len(music.queue) - 1) if music.current - 1 < 0 else (music.current - 1)
    )
    await cmd.msg.reply(content="went back a track")


@cmds.new
@cmds.args
async def goto(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """go to a specific index ( starting from 1 ) in the queue, takes arg [idx], which is the index"""

    try:
        idx: int = int(cmd.args) - 1
    except ValueError:
        await cmd.msg.reply(content="invalid number")
        return

    if idx < 0 or idx > len(music.queue):
        await cmd.msg.reply(content="invalid index")
        return

    music.current = idx
    await cmd.msg.reply(content=f"set index to {cmd.args}")


@cmds.new
async def remove(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """remove a track from the queue, takes optional arg [idx] which is the queue index starting from 1, default is current"""

    if not cmd.args:
        idx = music.current
    else:
        try:
            idx: int = int(cmd.args) - 1
        except ValueError:
            await cmd.msg.reply(content="invalid number")
            return

        if idx < 0 or idx > len(music.queue):
            await cmd.msg.reply(content="invalid index")
            return

    if idx <= music.current:
        music.current -= 1

    await cmd.msg.reply(content=f"removed {music.queue.pop(idx)} from the queue")


@cmds.new
async def pop(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """pop / remove last element from the queue"""

    await cmd.msg.reply(
        content=f"removed {music.queue.pop() if music.queue else 'nothing'} from the queue"
    )


@cmds.new
async def volume(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """set the volume, takes an optional argument `volume` which is the volume in percent, \
like volume 69.1 = 69.1%, if no volume is supplied it shows current volume"""

    if music.voice.source is None:
        await cmd.msg.reply(content="i am currently not playing anything")
        return

    if not cmd.args:
        await cmd.msg.reply(
            content=f"current volume : {music.voice.source.volume * 100}%\ndefault volume : {const.MUSIC_DEFAULT_VOL * 100}%"
        )
        return

    try:
        vol: float = float(cmd.args.removesuffix("%"))
    except ValueError:
        await cmd.msg.reply(content="not a valid floating point integer")
        return

    if vol < 0 or vol > 100:
        await cmd.msg.reply(content="this is not a valid volume")
        return

    music.voice.source.volume = music.volume = vol / 100  # type: ignore

    await cmd.msg.reply(
        content=f"volume set to {vol}% ( {music.voice.source.volume} )"  # type: ignore
    )


@cmds.new
async def shuffle(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """shuffle the current queue"""

    RAND.shuffle(music.queue)
    music.current = -1

    await cmd.msg.reply(content="shuffled the queue")


@cmds.new
async def current(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """display the current playing track"""

    await cmd.msg.reply(
        content=f"currently playing {music.queue[music.current]} ( {music.current + 1}/{len(music.queue)} )"
        + (
            ""
            if music.voice.source is None
            else f" audio : ||{music.voice.source.data['url']}||"
        )
    )


@cmds.nnew
async def random(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """add random ai suggested song, takes an optional argument [n] for number of songs to generate, for example `random 10`"""

    n: int = 1

    if cmd.args:
        try:
            n = int(cmd.args)
        except ValueError:
            await cmd.msg.reply(content=f"`{cmd.args}` isnt a valid integer")
            return

    n = min(n, const.MUSIC_AI_MAX)

    await cmd.msg.reply(
        content=f"adding {n} ( value is wrapped to {const.MUSIC_AI_MAX} ) songs"
    )

    prev: list[str] = []
    nl: str = "\n"

    for idx in range(n):
        song: str = ""

        for _ in range(const.MUSIC_AI_TRIES):
            try:
                song = (
                    (
                        await asyncio.wait_for(
                            gpt3.Completion.create(
                                f"""{const.MUSIC_AI_GEN}

Your previous responses were:
{nl.join(prev)[-(const.MESSAGE_WRAP_LEN - len(const.MUSIC_AI_GEN)):] if prev else '<none>'}"""  # type: ignore
                            ),
                            timeout=15,
                        )
                    )[: const.MUSIC_AI_LIMIT]
                    .strip()
                    .splitlines()
                    + [""]
                )[0]
            except Exception:
                pass

            if song:
                break

            await asyncio.sleep(5)

        if song:
            prev.append(song)

            await cmd.msg.reply(
                content=f"[{idx + 1}/{n}] adding an ai suggested song, `{song}`, to the queue"
            )

            Thread(target=music._play, args=(song,), daemon=True).start()

        await asyncio.sleep(2)


@cmds.nnew
async def loop(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """toggles loop status for the queue"""

    music.loop = not music.loop
    await cmd.msg.reply(content=f"loop is now set to `{music.loop}`")


@cmds.nnew
async def repeat(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """toggles repeat status for currennt audio"""

    music.repeat = not music.repeat
    await cmd.msg.reply(content=f"repeat is now set to `{music.repeat}`")


@cmds.nnew
async def info(music: typing.Any, cmd: mcmdmgr.MusicCommand) -> None:
    """show music bot info"""

    await cmd.msg.reply(
        content=f"""bot : {'me' if music.b.user is None else music.b.user.mention}
thread : {music.thread.jump_url}
voice chat : {music.voice.channel.jump_url}
yt_dl : {music.ytdl.__module__}
queue length : {len(music.queue)}
command queue length : {len(music.cqueue)}
current track index from 0 : {music.current} ( <{music.queue[music.current] if music.queue else 'nothing playing right now'}> )
running : {music.run}
loop : {music.loop}
repeat : {music.repeat}
playing : {music.voice.is_playing()}
paused : {music.voice.is_paused()}
latency : {music.voice.average_latency * 1000} ms
volume : {music.voice.source.volume * 100}%"""
    )
