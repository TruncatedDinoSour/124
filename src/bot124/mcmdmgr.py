#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""music commands manager"""

import textwrap
import traceback
import typing
from dataclasses import dataclass
from functools import wraps

from discord import AllowedMentions, Message

from . import const


@dataclass
class MusicCommand:
    args: str
    cmd: str
    msg: Message


@dataclass
class MusicCommands:
    def __init__(self) -> None:
        self.cmds: dict[
            str, typing.Callable[[typing.Any, MusicCommand], typing.Any]
        ] = {}

        async def _help(_: typing.Any, cmd: MusicCommand) -> None:
            """display help"""

            for page in textwrap.wrap(
                "help for music functions\n\n"
                "- to add music to the queue just type your search query or send a youtube url to your song or playlist\n"
                f"- if u wanna say smt in the chat without the bot seeing start ur message with `{const.MUSIC_COMMENT}`, for example "
                f"`{const.MUSIC_COMMENT} this is my comment`\n"
                "\n"
                + "".join(
                    f"- {name} -- {fun.__doc__ or 'no help provided'}\n"
                    for name, fun in self.cmds.items()
                ),
                const.MESSAGE_WRAP_LEN,
                replace_whitespace=False,
            ):
                await cmd.msg.reply(
                    content=page,
                    allowed_mentions=AllowedMentions.none(),
                )

        self.cmds["help"] = _help
        self.music: typing.Any = None

    def new(
        self, fn: typing.Callable[[typing.Any, MusicCommand], typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        @wraps(fn)
        async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            assert (
                self.music is not None
            ), "music command manager is being used pre-initialization"

            if not self.music.queue:
                await args[1].msg.reply(content="no queue found")
                return

            return await fn(*args, **kwargs)

        self.cmds[fn.__name__] = wrapper
        return wrapper

    def nnew(
        self, fn: typing.Callable[[typing.Any, MusicCommand], typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        @wraps(fn)
        async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            assert (
                self.music is not None
            ), "music command manager is being used pre-initialization"
            return await fn(*args, **kwargs)

        self.cmds[fn.__name__] = wrapper
        return wrapper

    def args(
        self, fn: typing.Callable[[typing.Any, MusicCommand], typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        @wraps(fn)
        async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if not args[1].args:
                await args[1].msg.reply(content="missing arguments")
                return

            return await fn(*args, **kwargs)

        return wrapper

    def init(self, music: typing.Any) -> None:
        self.music = music

    async def push(self, cmd: MusicCommand) -> None:
        try:
            await self.cmds[cmd.cmd](self.music, cmd)
        except Exception:
            traceback.print_exc()
