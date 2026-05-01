from __future__ import annotations

import os
from dataclasses import dataclass

from gdey0154f51.constants import PinConfig, SpiConfig


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


@dataclass(frozen=True)
class PiServerConfig:
    api_key: str
    bind_host: str
    port: int
    queue_max_size: int
    busy_timeout_s: float
    pin_config: PinConfig
    spi_config: SpiConfig

    @classmethod
    def from_env(cls) -> "PiServerConfig":
        pin_config = PinConfig(
            rst=_get_int("PIN_RST", 17),
            dc=_get_int("PIN_DC", 25),
            cs=_get_int("PIN_CS", 8),
            busy=_get_int("PIN_BUSY", 24),
        )
        spi_config = SpiConfig(
            bus=_get_int("SPI_BUS", 0),
            device=_get_int("SPI_DEVICE", 0),
            max_speed_hz=_get_int("SPI_SPEED", 2_000_000),
            mode=_get_int("SPI_MODE", 0),
        )
        return cls(
            api_key=os.getenv("API_KEY", "dev-api-key"),
            bind_host=os.getenv("BIND_HOST", "0.0.0.0"),
            port=_get_int("PORT", 8765),
            queue_max_size=_get_int("QUEUE_MAX_SIZE", 100),
            busy_timeout_s=_get_float("BUSY_TIMEOUT_S", 20.0),
            pin_config=pin_config,
            spi_config=spi_config,
        )
