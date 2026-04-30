from __future__ import annotations

from gdey0154f51 import Color, GDEY0154F51


def main() -> None:
    with GDEY0154F51.from_rpi() as epd:
        # Quick wiring sanity check.
        epd.fill(Color.WHITE, auto_sleep=True)


if __name__ == "__main__":
    main()
