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

TRUTHS: Final[tuple[str, ...]] = (
    "what is a weird food that you love ?",
    "what terrible film or show is your guilty pleasure ?",
    "what was your biggest childhood fear ?",
    "what is the first letter of your crushs name ?",
    "what is the worst grade you received for a class in school / college ?",
    "what is the biggest lie youve ever told ?",
    "have you ever accidentally hit ( or wanted to hit ) something ( or someone ! ) with your car ?",
    "have you ever broken an expensive item ?",
    "what is one thing youd change about your appearance if you could ?",
    "if you suddenly had a million dollars, how would you spend it ?",
    "who is the best teacher youve ever had and why ?",
    "what is the worst food youve ever tasted ?",
    "what is the weirdest way youve met someone you now consider a close friend ?",
    "what is the most embarrassing thing youve posted on social media ?",
    "who was / is your first celebrity crush ?",
    "have you ever revealed a friends secret to someone else ?",
    "how many kids do you want to have one day ( or how many did you want to have growing up ) ?",
    "if you could only eat one meal for the rest of your life, what would it be ?",
    "what is a secret you had as a child that you never told your parents ?",
    "what is your favorite book of all time ?",
    "what is the last text message you sent your best friend ?",
    "what is something you would do if you knew there were no consequences ?",
    "what is the worst physical pain youve ever been in ?",
    "personality-wise, are you more like your mom or your dad ?",
    "when is the last time you apologized ( and what did you do ) ?",
    "have you ever reported someone for doing something wrong ( either to the police or at work / school ) ?",
    "if your house caught on fire and you could only save three things ( besides people ), what would they be ?",
    "if you could pick one other player to take with you to a deserted island, who would it be ?",
    "what sport or hobby do you wish you wouldve picked up as a child ?",
    "have you ever stolen anything ?",
    "have you ever been kicked out of a store, restaurant, bar, event, etc ?",
    "what is the worst date youve ever had ?",
    "what is the weirdest thing youve ever done in public ?",
    "what is the last excuse you used to cancel plans ?",
    "what is the biggest mistake youve ever made at school or work ?",
    "which player would survive the longest in a horror / apocalypse film, and who would be the first one to die ?",
    "what is the dirtiest room / area of your house ?",
    "which of your family members annoys you the most ?",
    "when is the last time you cried ?",
    "when is the last time you made someone else cry ?",
    "what is the longest youve ever gone without showering ?",
    "what is the worst date youve ever been on ?",
    "when is the last time you did something technically illegal ?",
    "if you could pick anyone in the world to be president, who would you choose ?",
    "how many times do you wear your jeans before you wash them ?",
    "do you pee in pools ?",
    "if someone went through your closet, what is the weirdest thing theyd find ?",
    "have you ever lied about your age ?",
    "besides your phone, whats the one item in your house you couldnt live without ?",
    "what is the biggest fight youve ever been in with a friend ?",
    "when did you have your first kiss ?",
)

DARES: Final[tuple[str, ...]] = (
    "let another player to choose your discord profile picture for 24 hours",
    "talk in uwu language for the next 20 minutes",
    "act like an animal for the next minute",
    "show your youtube search history for the group",
    "pair everyone here up into couples",
    "describe your crush, but dont give it away",
    "text the first six people in your message history 'a' and dont reply if they bring it up",
    "show everyone here your last 10 search engine searches",
    "show your most used emojis in your keyboard",
    "make a poem using the words orange and moose",
    "tell the other players something they dont know about you",
    "close your eyes and send a blind message to a random person",
    "show the last dm you sent without context",
    "show the list of people in your dms",
    "speak only in emojis for the next 5 minutes",
    "name one thing you would change about each person here",
    "send a song you're embarrassed to listen to",
    "rate everyone here 1-10 in terms of personality",
    "change your nickname / username to whatever the group wants",
    "do your best impersonation of someone here",
    "write a ( short ) poem for someone here",
    "post the oldest photo on your phone",
    "post the newest photo on your phone",
    "text the last 6 people in your dms 'i love you'",
    "send picture of your pet",
    "type with only one hand for the next minute",
    'text your best friend "something crazy just happened" and dont respond',
    "send one of your favourite playlists",
    "send your favourite joke",
    "show the group the last song youve listened to",
    "show everyone the last youtube video you watched",
    "share your wallpaper",
    "send a selfie",
    "change your discord pfp to whatever the group decides",
    "have everyone here list something they like about you",
    "uwuify your username / nickname and set it as your username / nickname",
    "rickroll someone",
    "let the group decide your status for 3 days",
    "list three things you like about your crush",
    "ask someone random for a hug",
    "show the group a picture of one person you find very attractive",
    "what really embarrassing thing still haunts you to this day",
    "play a song of the next persons choosing",
    "send the last meme you saved to your phone",
    "DM the person at the bottom of your DMs list",
    "message someone you argued with and tell them that youre sorry",
    "name as many types of food as you can",
    "have a matching pfp with someone for 3 days",
    "send the fifth person in your message history 20 seconds of keyboard spam",
    "list everyone as the emoji( s ) you think best fits them",
    "imitate a behaviour of who you like",
)
