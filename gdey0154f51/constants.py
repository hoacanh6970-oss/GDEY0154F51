from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

WIDTH = 200
HEIGHT = 200
PIXELS_PER_BYTE = 4
BUFFER_SIZE = WIDTH * HEIGHT // PIXELS_PER_BYTE


class Color(IntEnum):
    BLACK = 0
    WHITE = 1
    YELLOW = 2
    RED = 3


@dataclass(frozen=True)
class PinConfig:
    rst: int = 17
    dc: int = 25
    cs: int = 8
    busy: int = 24


@dataclass(frozen=True)
class SpiConfig:
    bus: int = 0
    device: int = 0
    max_speed_hz: int = 2_000_000
    mode: int = 0
    use_hardware_cs: bool = True
    backend: str = "hardware"
    soft_sck_pin: int = 11
    soft_mosi_pin: int = 10
    soft_bit_delay_us: int = 1
    soft_cs_gap_us: int = 10


FILL_BYTE_BY_COLOR: dict[Color, int] = {
    Color.BLACK: 0x00,
    Color.WHITE: 0x55,
    Color.YELLOW: 0xAA,
    Color.RED: 0xFF,
}

# Arduino demo image encoding uses: 0=white, 1=yellow, 2=red, 3=black.
DEMO_TO_NATIVE_2BIT: dict[int, int] = {
    0: int(Color.WHITE),
    1: int(Color.YELLOW),
    2: int(Color.RED),
    3: int(Color.BLACK),
}
