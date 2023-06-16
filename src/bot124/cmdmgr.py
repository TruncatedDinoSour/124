#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""command manager"""

import typing
from functools import wraps

import discord
import discord.app_commands  # type: ignore

__all__: tuple[str] = ("CommandManager",)


class CommandManager:
    def __init__(self) -> None:
        self.cmds: list[typing.Callable[..., typing.Any]] = []
        self.b: discord.Client = None  # type: ignore

    def new(
        self, fn: typing.Callable[..., typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        @wraps(fn)
        async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            assert (
                self.b is not None
            ), "command manager is being used pre-initialization"
            return await fn(*args, **kwargs)

        self.cmds.append(wrapper)
        return wrapper

    def register_commands(self, ct: discord.app_commands.CommandTree) -> None:
        while self.cmds:
            cmd: typing.Callable[..., typing.Any] = self.cmds.pop()
            ct.command(  # type: ignore
                name=cmd.__name__, description=cmd.__doc__ or "no help provided"
            )(cmd)

    def init(self, ct: discord.app_commands.CommandTree, b: discord.Client) -> None:
        self.b = b
        self.register_commands(ct)
