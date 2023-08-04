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
import rebelai.ai.inferkit
import rebelai.ai.pollinations
import rebelai.ai.prodia
import rebelai.enums

from . import util


class TextAI(Enum):
    @staticmethod
    async def _alpaca7(prompt: str) -> typing.Optional[str]:
        return await rebelai.ai.alpaca.alpaca_7b(
            prompt,
            request_args=await util.get_proxies(),
        )

    @staticmethod
    async def _deepai(prompt: str) -> str:
        return (
            await rebelai.ai.deepai.deepai(
                rebelai.enums.DeepAIModel.TEXT,
                {"text": prompt},
                request_args=await util.get_proxies(),
            )
        )["output"]

    @staticmethod
    async def _inferkit(prompt: str) -> typing.Optional[str]:
        return await rebelai.ai.inferkit.standard(
            prompt,
            length=1000,
            request_args=await util.get_proxies(),
        )

    alpaca7 = (_alpaca7,)
    deepai = (_deepai,)
    gpt3 = (rebelai.ai.gpt.gpt3,)
    gpt4 = (rebelai.ai.gpt.gpt4,)
    inferkit = (_inferkit,)


class ImageAI(Enum):
    @staticmethod
    async def _pollinations(prompt: str) -> bytes:
        return await rebelai.ai.pollinations.pollinations(  # type: ignore
            prompt,
            request_args=await util.get_proxies(),
        )

    pollinations = (_pollinations,)
    prodia = (rebelai.ai.prodia.prodia,)


async def gen_ai_text(
    prompt: str,
    model: TextAI = TextAI.gpt4,
) -> str:
    r: typing.Optional[str] = None

    for _ in range(3):
        try:
            r: typing.Optional[str] = await model.value[0](prompt)
            break
        except Exception:
            time.sleep(0.5)

    return (r or "")[:2000].strip()


async def gen_ai_img(
    prompt: str,
    model: ImageAI = ImageAI.pollinations,
) -> discord.File:
    r: bytes = bytes()

    try:
        r = await model.value[0](prompt)
    except Exception:
        time.sleep(0.5)

    return discord.File(
        BytesIO(r),  # type: ignore
        f"124_{model.name}_generation_{datetime.datetime.utcnow()}.png",
    )
