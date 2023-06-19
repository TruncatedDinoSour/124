#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124bot constants"""

from typing import Final

from reactionmenu import ReactionButton  # type: ignore

BOT_DB_URL: Final[str] = "sqlite:///bot.db?check_same_thread=False"
MESSAGE_WRAP_LEN: Final[int] = 1900
BUTTONS: Final[tuple[ReactionButton, ...]] = (
    ReactionButton.go_to_first_page(),
    ReactionButton.back(),
    ReactionButton.next(),
    ReactionButton.go_to_last_page(),
)
MAX_PRESENCE_LEN: Final[int] = 64
OK_CHANNEL: Final[str] = "ok"
RULES_CHANNEL: Final[str] = "rules"
REAL_RULES_ID: Final[tuple[str, ...]] = ("(real rule)", "( real rule )")
FAKE_RULES_ID: Final[tuple[str, ...]] = ("(fake rule)", "( fake rule )")
MIN_WORDCLOUD_LIMIT: Final[int] = 500
WORDCLOUD_WRAP: Final[int] = 540
MIN_RULES_LIMIT: Final[int] = 1000
MIN_CONFESSION_LIMIT: Final[int] = 500
STARBOARD_WRAP_LEN: Final[int] = MESSAGE_WRAP_LEN - 128

MSGS_W: Final[float] = 0.1
VCS_W: Final[float] = 0.2
WC_W: Final[float] = 0.15
REACT_GET_W: Final[float] = 0.2
REACT_POST_W: Final[float] = 0.1
STAR_W: Final[float] = 0.5

REACT_POST_K: Final[float] = 0.7

K_MULT: Final[float] = 300
SCORE_MULT: Final[float] = 50

SCORE_E: Final[float] = 0.69

STAR_EMOJI: Final[str] = "⭐"
STAR_COUNT: Final[int] = 3
