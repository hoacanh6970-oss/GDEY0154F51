from __future__ import annotations

import time

from gdey0154f51 import Color, GDEY0154F51


def main() -> None:
    with GDEY0154F51.from_rpi() as epd:
        for color in (Color.BLACK, Color.WHITE, Color.YELLOW, Color.RED):
            epd.fill(color, auto_sleep=True)
            time.sleep(2)


if __name__ == "__main__":
    main()
