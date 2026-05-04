#!/usr/bin/env python3
from __future__ import annotations

import argparse

from gdey0154f51 import GDEY0154F51, PinConfig, SpiConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Display an image on GDEY0154F51 via Raspberry Pi"
    )
    parser.add_argument("--image", required=True, help="Image path")
    parser.add_argument(
        "--fit", default="contain", choices=["contain", "cover", "stretch"]
    )
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270])
    parser.add_argument("--no-dither", action="store_true", help="Disable dithering")
    parser.add_argument(
        "--no-sleep", action="store_true", help="Do not enter deep sleep after refresh"
    )
    parser.add_argument(
        "--fast-update",
        action="store_true",
        help="Use Arduino fast full-update initialization sequence",
    )

    parser.add_argument("--spi-bus", type=int, default=0)
    parser.add_argument("--spi-device", type=int, default=0)
    parser.add_argument("--spi-speed", type=int, default=2_000_000)
    parser.add_argument(
        "--spi-backend",
        default="hardware",
        choices=["hardware", "software"],
        help="SPI backend: spidev hardware or GPIO bit-banged software SPI",
    )
    parser.add_argument("--soft-sck", type=int, default=11)
    parser.add_argument("--soft-mosi", type=int, default=10)
    parser.add_argument("--soft-bit-delay-us", type=int, default=1)
    parser.add_argument("--soft-cs-gap-us", type=int, default=10)
    parser.add_argument(
        "--manual-cs",
        action="store_true",
        help="Use GPIO-managed CS instead of spidev hardware chip select",
    )

    parser.add_argument("--pin-rst", type=int, default=17)
    parser.add_argument("--pin-dc", type=int, default=25)
    parser.add_argument("--pin-cs", type=int, default=8)
    parser.add_argument("--pin-busy", type=int, default=24)
    parser.add_argument(
        "--busy-active-low",
        action="store_true",
        help="Treat BUSY=0 as ready (some board revisions use inverted polarity)",
    )
    parser.add_argument(
        "--no-busy-auto-fallback",
        action="store_true",
        help="Disable automatic BUSY polarity fallback after timeout",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pins = PinConfig(
        rst=args.pin_rst, dc=args.pin_dc, cs=args.pin_cs, busy=args.pin_busy
    )
    spi = SpiConfig(
        bus=args.spi_bus,
        device=args.spi_device,
        max_speed_hz=args.spi_speed,
        mode=0,
        use_hardware_cs=not args.manual_cs,
        backend=args.spi_backend,
        soft_sck_pin=args.soft_sck,
        soft_mosi_pin=args.soft_mosi,
        soft_bit_delay_us=args.soft_bit_delay_us,
        soft_cs_gap_us=args.soft_cs_gap_us,
    )

    epd = GDEY0154F51.from_rpi(
        pin_config=pins,
        spi_config=spi,
        busy_ready_level=0 if args.busy_active_low else 1,
        busy_auto_fallback=not args.no_busy_auto_fallback,
    )
    try:
        epd.display_image(
            args.image,
            dither=not args.no_dither,
            fit=args.fit,
            rotate=args.rotate,
            auto_sleep=not args.no_sleep,
            fast_update=args.fast_update,
        )
        print("display refresh complete")
    finally:
        epd.close()


if __name__ == "__main__":
    main()
