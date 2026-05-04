from __future__ import annotations

import time
from dataclasses import dataclass

from .constants import PinConfig, SpiConfig
from .interfaces import GpioBus
from .interfaces import SpiBus


class RPiSpiBus:
    """SPI backend implemented with spidev."""

    def __init__(self, config: SpiConfig) -> None:
        self._config = config
        self._spi = None
        self.uses_hardware_cs = config.use_hardware_cs

    def open(self) -> None:
        if self._spi is not None:
            return
        import spidev  # type: ignore

        spi = spidev.SpiDev()
        spi.open(self._config.bus, self._config.device)
        spi.max_speed_hz = self._config.max_speed_hz
        spi.mode = self._config.mode
        try:
            spi.no_cs = not self._config.use_hardware_cs
        except AttributeError:
            pass
        self._spi = spi

    def write(self, data: bytes) -> None:
        if self._spi is None:
            raise RuntimeError("SPI bus is not opened")
        if not data:
            return
        self._spi.xfer2(list(data))

    def close(self) -> None:
        if self._spi is not None:
            self._spi.close()
            self._spi = None


class RPiSoftSpiBus:
    """Software SPI backend implemented by bit-banging GPIO."""

    def __init__(
        self,
        gpio: GpioBus,
        config: SpiConfig,
        sleep_fn=time.sleep,
    ) -> None:
        self._gpio = gpio
        self._config = config
        self._sleep_fn = sleep_fn
        self._is_open = False
        self.uses_hardware_cs = False

    def open(self) -> None:
        if self._is_open:
            return
        if self._config.mode != 0:
            raise ValueError("software SPI currently supports mode=0 only")
        if self._config.soft_bit_delay_us < 0:
            raise ValueError("soft_bit_delay_us must be >= 0")
        self._gpio.setup_output(self._config.soft_sck_pin)
        self._gpio.setup_output(self._config.soft_mosi_pin)
        self._gpio.write(self._config.soft_sck_pin, 0)
        self._gpio.write(self._config.soft_mosi_pin, 0)
        self._is_open = True

    def write(self, data: bytes) -> None:
        if not self._is_open:
            raise RuntimeError("software SPI bus is not opened")
        if not data:
            return
        delay_s = self._config.soft_bit_delay_us / 1_000_000.0
        for value in data:
            for bit_index in range(7, -1, -1):
                bit = (value >> bit_index) & 0x01
                self._gpio.write(self._config.soft_mosi_pin, bit)
                if delay_s > 0:
                    self._sleep_fn(delay_s)
                self._gpio.write(self._config.soft_sck_pin, 1)
                if delay_s > 0:
                    self._sleep_fn(delay_s)
                self._gpio.write(self._config.soft_sck_pin, 0)

    def close(self) -> None:
        self._is_open = False


class RPiGpioBus:
    """GPIO backend implemented with RPi.GPIO in BCM mode."""

    def __init__(self) -> None:
        self._gpio = None

    def open(self) -> None:
        if self._gpio is not None:
            return
        import RPi.GPIO as GPIO  # type: ignore

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self._gpio = GPIO

    def setup_output(self, pin: int) -> None:
        if self._gpio is None:
            raise RuntimeError("GPIO is not opened")
        self._gpio.setup(pin, self._gpio.OUT)

    def setup_input(self, pin: int) -> None:
        if self._gpio is None:
            raise RuntimeError("GPIO is not opened")
        self._gpio.setup(pin, self._gpio.IN)

    def write(self, pin: int, value: int) -> None:
        if self._gpio is None:
            raise RuntimeError("GPIO is not opened")
        self._gpio.output(pin, value)

    def read(self, pin: int) -> int:
        if self._gpio is None:
            raise RuntimeError("GPIO is not opened")
        return int(self._gpio.input(pin))

    def cleanup(self) -> None:
        if self._gpio is not None:
            self._gpio.cleanup()
            self._gpio = None


@dataclass
class RPiHAL:
    spi: SpiBus
    gpio: RPiGpioBus


def create_rpi_hal(
    pin_config: PinConfig | None = None,
    spi_config: SpiConfig | None = None,
) -> RPiHAL:
    _ = pin_config  # Reserved for future board profiles.
    config = spi_config or SpiConfig()
    gpio = RPiGpioBus()
    gpio.open()
    backend = config.backend.lower()
    if backend == "hardware":
        spi = RPiSpiBus(config)
    elif backend == "software":
        spi = RPiSoftSpiBus(gpio=gpio, config=config)
    else:
        raise ValueError(f"unsupported SPI backend: {config.backend}")
    spi.open()
    return RPiHAL(spi=spi, gpio=gpio)
