#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""124"""

import os
import sys
import typing
from warnings import filterwarnings as filter_warnings

from bot124 import Bot124


def main() -> int:
    """entry/main function"""

    token: typing.Optional[str]

    print(
        "\33[31m\33[1m!!! this version of the 124 bot is no longer supported, use https://ari-web.xyz/gh/124tg instead\33[0m",
        file=sys.stderr,
    )

    if (token := os.environ.get("D")) is None:
        print(
            "no discord token found ( `D` env var )\n$ export D='your-discord-token ...'",
            file=sys.stderr,
        )
        return 1

    Bot124().run(token)

    return 0


if __name__ == "__main__":
    assert main.__annotations__.get("return") is int, "main() should return an integer"

    filter_warnings("error", category=Warning)
    raise SystemExit(main())
