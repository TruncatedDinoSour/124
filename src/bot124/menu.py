#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124 bot menu utils"""

import textwrap

import discord
from reactionmenu import ViewMenu  # type: ignore

from . import const


async def text_menu(msg: discord.interactions.Interaction, text: str) -> None:
    if len(text) <= const.MESSAGE_WRAP_LEN:
        await msg.response.defer()
        await msg.followup.send(content=text)
        return

    menu: ViewMenu = ViewMenu(msg, menu_type=ViewMenu.TypeText, style="$/&")
    menu.add_pages(
        textwrap.wrap(text, const.MESSAGE_WRAP_LEN, replace_whitespace=False)
    )
    menu.add_buttons(const.VIEW_BUTTONS)
    await menu.start()
