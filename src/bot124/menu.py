#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot menu utils"""

import textwrap

import discord
from reactionmenu import ReactionMenu  # type: ignore

from . import const


async def text_menu(
    msg: discord.interactions.Interaction, text: str, wrap: int = const.MESSAGE_WRAP_LEN
) -> None:
    if len(text) <= const.MESSAGE_WRAP_LEN:
        await msg.response.defer()
        await msg.followup.send(content=text)
        return

    menu: ReactionMenu = ReactionMenu(msg, menu_type=ReactionMenu.TypeText, style="$/&")
    menu.add_pages(textwrap.wrap(text, wrap, replace_whitespace=False))
    menu.add_buttons(const.BUTTONS)
    await menu.start()
