#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""music commands manager"""

import textwrap
import typing
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import traceback

from discord import AllowedMentions, Message

from . import const


class MusicCommandT(Enum):
    QUIT = "quit"
    CLEAR = "clear"
    QUEUE = "queue"
    STOP = "stop"
    PLAY = "play"
    SKIP = "skip"
    VOLUME = "volume"
    SHUFFLE = "shuffle"
    CURRENT = "current"
    HELP = "help"


@dataclass
class MusicCommand:
    args: str
    type: MusicCommandT
    msg: Message


@dataclass
class MusicCommands:
    def __init__(self) -> None:
        self.cmds: dict[
            MusicCommandT, typing.Callable[[typing.Any, MusicCommand], typing.Any]
        ] = {}

        async def _help(_: typing.Any, cmd: MusicCommand) -> None:
            """display help"""

            for page in textwrap.wrap(
                "help for music functions\n\n"
                + "".join(
                    f"- {type.value} -- {fun.__doc__ or 'no help provided'}\n"
                    for type, fun in self.cmds.items()
                ),
                const.MESSAGE_WRAP_LEN,
                replace_whitespace=False,
            ):
                await cmd.msg.reply(
                    content=page,
                    allowed_mentions=AllowedMentions.none(),
                )

        self.cmds[MusicCommandT.HELP] = _help

        self.music: typing.Any = None

    def new(
        self, fn: typing.Callable[[typing.Any, MusicCommand], typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        @wraps(fn)
        async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            assert (
                self.music is not None
            ), "music command manager is being used pre-initialization"
            return await fn(*args, **kwargs)

        self.cmds[MusicCommandT(fn.__name__)] = wrapper
        return wrapper

    def init(self, music: typing.Any) -> None:
        self.music = music

    async def push(self, cmd: MusicCommand) -> None:
        try:
            await self.cmds[cmd.type](self.music, cmd)
        except Exception:
            traceback.print_exc()
