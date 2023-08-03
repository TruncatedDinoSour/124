#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai implementation"""

import datetime
import time
import typing
from enum import Enum
from io import BytesIO

import discord
import rebelai.ai.alpaca
import rebelai.ai.deepai
import rebelai.ai.gpt
import rebelai.ai.pollinations
import rebelai.ai.prodia
import rebelai.enums

from . import util


class TextAI(Enum):
    alpaca7 = (
        lambda prompt: rebelai.ai.alpaca.alpaca_7b(  # type: ignore
            prompt,  # type: ignore
            request_args=util.get_proxies(),
        ),
    )
    deepai = (
        lambda prompt: rebelai.ai.deepai.deepai(  # type: ignore
            rebelai.enums.DeepAIModel.TEXT,
            {"text": prompt},
            request_args=util.get_proxies(),
        )["output"],
    )
    gpt3 = (rebelai.ai.gpt.gpt3,)
    gpt4 = (rebelai.ai.gpt.gpt4,)


class ImageAI(Enum):
    pollinations = (
        lambda prompt: rebelai.ai.pollinations.pollinations(  # type: ignore
            prompt,  # type: ignore
            request_args=util.get_proxies(),
        ),
    )
    prodia = (rebelai.ai.prodia.prodia,)


def gen_ai_text(
    prompt: str,
    model: TextAI = TextAI.gpt4,
) -> str:
    r: typing.Optional[str] = None

    for _ in range(3):
        try:
            r: typing.Optional[str] = model.value[0](prompt)  # type: ignore
            break
        except Exception:
            time.sleep(0.5)

    return (r or "")[:2000].strip()


def gen_ai_img(
    prompt: str,
    model: ImageAI = ImageAI.pollinations,
) -> discord.File:
    r: bytes = bytes()

    for _ in range(3):
        try:
            r = model.value[0](prompt)  # type: ignore
            break
        except Exception:
            time.sleep(0.5)

    return discord.File(
        BytesIO(r),  # type: ignore
        f"124_{model.name}_generation_{datetime.datetime.utcnow()}.png",
    )
