#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124bot constants"""

from math import cos, e, pi
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

# random constants for obscurity ig

BYTES_WEIGHT: Final[float] = (1 + 5**0.5) / 9.2
VC_JOIN_WEIGHT: Final[float] = BYTES_WEIGHT * 1.05
VC_TIME_WEIGHT: Final[float] = e / pi / 3.5
MSGS_WEIGHT: Final[float] = (BYTES_WEIGHT + VC_JOIN_WEIGHT + VC_TIME_WEIGHT) / 5.5
SCORE_MULT: Final[float] = 0.1 - cos(e) * 113
