#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124bot menu utils"""

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
        try:
            await msg.response.defer()  # type: ignore
        except Exception:
            pass

        await msg.followup.send(  # type: ignore
            content=pages[0],
            allowed_mentions=discord.mentions.AllowedMentions.none(),
        )
        return

    menu: ReactionMenu = ReactionMenu(
        msg,
        menu_type=ReactionMenu.TypeText,
        style="$/&",
        allowed_mentions=discord.mentions.AllowedMentions.none(),
    )
    menu.add_pages(pages)
    menu.add_buttons(const.BUTTONS)
    await menu.start()


def wrap_text(text: str, wrap: int = const.MESSAGE_WRAP_LEN) -> list[str]:
    return textwrap.wrap(text, wrap, replace_whitespace=False)


async def text_menu(
    msg: discord.interactions.Interaction, text: str, wrap: int = const.MESSAGE_WRAP_LEN
) -> None:
    await menu(msg, wrap_text(text, wrap))
