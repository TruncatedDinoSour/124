#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai implementation"""

import datetime
import time
import typing
from enum import Enum
from io import BytesIO

import discord
import iso639  # type: ignore
import rebelai.ai.alpaca
import rebelai.ai.deepai
import rebelai.ai.deepl
import rebelai.ai.gpt
import rebelai.ai.inferkit
import rebelai.ai.pollinations
import rebelai.ai.prodia
import rebelai.ai.h2o
import rebelai.enums

from . import const, util


class TextAI(Enum):
    @staticmethod
    async def _alpaca7(prompt: str) -> typing.Optional[str]:
        return await rebelai.ai.alpaca.alpaca_7b(
            prompt=prompt,
            request_args=await util.get_proxies(),
        )

    @staticmethod
    async def _deepai(prompt: str) -> str:
        # no more proxies :( request_args=await util.get_proxies(),

        return (
            await rebelai.ai.deepai.deepai(
                model=rebelai.enums.DeepAIModel.TEXT,
                data={"text": prompt},
            )
        )["output"]

    @staticmethod
    async def _inferkit(prompt: str) -> typing.Optional[str]:
        return await rebelai.ai.inferkit.standard(
            prompt=prompt,
            length=1000,
            request_args=await util.get_proxies(),
        )

    @staticmethod
    async def _falcon40(prompt: str) -> typing.Optional[str]:
        return await rebelai.ai.h2o.falcon_40b(
            prompt=prompt,
            request_args=await util.get_proxies(),
        )

    @staticmethod
    async def _gpt3(prompt: str) -> typing.Optional[str]:
        return await rebelai.ai.gpt.gpt3(
            prompt=prompt,
            request_args=await util.get_proxies(),
        )

    alpaca7 = (_alpaca7,)
    deepai = (_deepai,)
    gpt3 = (_gpt3,)
    gpt4 = (rebelai.ai.gpt.gpt4,)
    inferkit = (_inferkit,)
    falcon40 = (_falcon40,)


class ImageAI(Enum):
    @staticmethod
    async def _pollinations(prompt: str) -> bytes:
        return await rebelai.ai.pollinations.pollinations(  # type: ignore
            prompt=prompt,
            request_args=await util.get_proxies(),
        )

    pollinations = (_pollinations,)
    prodia = (rebelai.ai.prodia.prodia,)


async def gen_ai_text(
    prompt: str,
    model: TextAI = TextAI.gpt3,
    regen: bool = True,
) -> str:
    r: typing.Optional[str] = None

    for _ in range(3):
        try:
            r: typing.Optional[str] = await model.value[0](prompt=prompt)

            if r:
                break
        except Exception:
            if regen:
                return await gen_ai_text(
                    prompt,
                    TextAI.gpt4 if model is TextAI.gpt3 else TextAI.gpt3,
                    False,
                )

            time.sleep(0.5)

    return (r or "")[:2000].strip()


async def gen_ai_img(
    prompt: str,
    model: ImageAI = ImageAI.pollinations,
) -> discord.File:
    r: bytes = bytes()

    for _ in range(3):
        try:
            r = await model.value[0](prompt=prompt)

            if r:
                break
        except Exception:
            time.sleep(0.5)

    return discord.File(
        fp=BytesIO(r),
        filename=f"124_{model.name}_generation_{datetime.datetime.utcnow()}.png",
    )


async def translate(
    text: str,
    to_lang: str,
    from_lang: str = const.DEFAULT_TRANSLATE_SOURCE,
) -> tuple[str, ...]:
    if not all(iso639.is_valid639_1(lang) for lang in (from_lang, to_lang)):  # type: ignore
        return ("*not a valid language code*",)

    tr: typing.Union[tuple[str, ...], None] = None

    for _ in range(3):
        try:
            tr = await rebelai.ai.deepl.deepl(
                prompt=text,
                source_lang=from_lang,
                target_lang=to_lang,
                alternatives=3,
                request_args=await util.get_proxies(),
            )

            if tr:
                break
        except Exception:
            time.sleep(0.5)

    return tr or ("*no translation*",)
