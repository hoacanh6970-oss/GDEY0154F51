#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

from gdey0154f51 import Color, GDEY0154F51, PinConfig, SpiConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cycle 4 colors on GDEY0154F51")
    parser.add_argument(
        "--interval", type=float, default=2.0, help="seconds between color changes"
    )
    parser.add_argument("--repeat", type=int, default=1, help="number of loop rounds")

    parser.add_argument("--spi-speed", type=int, default=2_000_000)
    parser.add_argument(
        "--manual-cs",
        action="store_true",
        help="Use GPIO-managed CS instead of spidev hardware chip select",
    )
    parser.add_argument("--pin-rst", type=int, default=17)
    parser.add_argument("--pin-dc", type=int, default=25)
    parser.add_argument("--pin-cs", type=int, default=8)
    parser.add_argument("--pin-busy", type=int, default=24)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pins = PinConfig(
        rst=args.pin_rst, dc=args.pin_dc, cs=args.pin_cs, busy=args.pin_busy
    )
    spi = SpiConfig(
        max_speed_hz=args.spi_speed,
        use_hardware_cs=not args.manual_cs,
    )

    colors = [Color.BLACK, Color.WHITE, Color.YELLOW, Color.RED]

    epd = GDEY0154F51.from_rpi(pin_config=pins, spi_config=spi)
    try:
        for _ in range(args.repeat):
            for color in colors:
                print(f"displaying {color.name}")
                epd.fill(color, auto_sleep=True)
                time.sleep(args.interval)
    finally:
        epd.close()


if __name__ == "__main__":
    main()
