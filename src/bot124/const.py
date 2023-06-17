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

# random constants for obscurity ig

LEN_FACTOR_DIVISOR: Final[float] = 500
LEN_FACTOR_THRESHOLD: Final[float] = 250
VCS_FACTOR_DIVISOR: Final[float] = 1500
VCS_FACTOR_THRESHOLD: Final[float] = 1000
NEW_WORDS_WEIGHT_MULTIPLIER: Final[float] = 0.15
REACTION_WEIGHT_MULTIPLIER: Final[float] = 0.1
SCORE_DIVISOR: Final[float] = 10
LEN_FACTOR_DEF: Final[float] = 0.025
SCORE_MULT: Final[float] = 1e7
LEN_MULTIPLIER: Final[float] = 0.5
VCS_FACTOR_DEF: Final[float] = 0
SCORE_COEFFICIENT: Final[float] = 1.1
