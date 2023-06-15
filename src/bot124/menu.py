#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot menu utils"""

import textwrap
import typing

import discord
from reactionmenu import ReactionMenu  # type: ignore

from . import const


async def menu(
    msg: discord.interactions.Interaction,
    pages: typing.Sequence[str],
) -> None:
    if len(pages) == 1:
        await msg.response.defer()
        await msg.followup.send(content=pages[0])
        return

    menu: ReactionMenu = ReactionMenu(msg, menu_type=ReactionMenu.TypeText, style="$/&")
    menu.add_pages(pages)
    menu.add_buttons(const.BUTTONS)
    await menu.start()


async def text_menu(
    msg: discord.interactions.Interaction, text: str, wrap: int = const.MESSAGE_WRAP_LEN
) -> None:
    if len(text) <= const.MESSAGE_WRAP_LEN:
        await msg.response.defer()
        await msg.followup.send(content=text)
        return

    await menu(msg, textwrap.wrap(text, wrap, replace_whitespace=False))
