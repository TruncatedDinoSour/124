#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124bot constants"""

import re
from typing import Any, Final

from reactionmenu import ReactionButton  # type: ignore

BOT_DB_URL: Final[str] = "sqlite:///bot.db?check_same_thread=False"
MESSAGE_WRAP_LEN: Final[int] = 1900
BUTTONS: Final[tuple[ReactionButton, ...]] = (
    ReactionButton.go_to_first_page(),
    ReactionButton.back(),
    ReactionButton.go_to_page(),
    ReactionButton.next(),
    ReactionButton.go_to_last_page(),
)
MAX_PRESENCE_LEN: Final[int] = 64
OK_CHANNEL: Final[str] = "ok"
RULES_CHANNEL: Final[str] = "rules"
REAL_RULES_ID: Final[tuple[str, ...]] = ("(real rule)", "( real rule )")
FAKE_RULES_ID: Final[tuple[str, ...]] = ("(fake rule)", "( fake rule )")
WORDCLOUD_WRAP: Final[int] = 540
STARBOARD_WRAP_LEN: Final[int] = MESSAGE_WRAP_LEN - 128

MSGS_W: Final[float] = 0.1
VCS_W: Final[float] = 0.2
WC_W: Final[float] = 0.15
REACT_GET_W: Final[float] = 0.2
REACT_POST_W: Final[float] = 0.1
STAR_W: Final[float] = 0.5
OK_W: Final[float] = 0.1

REACT_POST_K: Final[float] = 0.7

K_MULT: Final[float] = 300
SCORE_MULT: Final[float] = 50

SCORE_E: Final[float] = 0.69
SCORE_DELTA_E: Final[float] = 0.34

STAR_EMOJI: Final[str] = "⭐"
STAR_COUNT: Final[int] = 3

SCORE_KICK_SLEEP: Final[int] = 6 * 60 * 60
SCORE_KICK_DELTA: Final[int] = 3 * 24 * 60 * 60

ANSI_REGEX: Final[re.Pattern[str]] = re.compile(
    r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
)

FFMPEG_OPTIONS: Final[dict[str, str]] = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}
YTDL_OPTIONS: Final[dict[str, Any]] = {
    "format": "bestaudio/best",
    "nocheckcertificate": True,
    "extract_flat": "in_playlist",
    "ignoreerrors": True,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "noprogress": True,
    "socket_timeout": 5,
    "socket_io_timeout": 10,
    "sleep_interval": 1,
    "max_sleep_interval": 5,
    "retries": 10,
    "fragment_retries": 10,
    "threads": 6,
    "nocheckcertificate": True,
    "geo_bypass": True,
}
