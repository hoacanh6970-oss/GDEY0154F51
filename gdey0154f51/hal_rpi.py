from __future__ import annotations

from dataclasses import dataclass

from .constants import PinConfig, SpiConfig


class RPiSpiBus:
    """SPI backend implemented with spidev."""

    def __init__(self, config: SpiConfig) -> None:
        self._config = config
        self._spi = None

    def open(self) -> None:
        if self._spi is not None:
            return
        import spidev  # type: ignore

        spi = spidev.SpiDev()
        spi.open(self._config.bus, self._config.device)
        spi.max_speed_hz = self._config.max_speed_hz
        spi.mode = self._config.mode
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
    spi: RPiSpiBus
    gpio: RPiGpioBus


def create_rpi_hal(
    pin_config: PinConfig | None = None,
    spi_config: SpiConfig | None = None,
) -> RPiHAL:
    _ = pin_config  # Reserved for future board profiles.
    spi = RPiSpiBus(spi_config or SpiConfig())
    gpio = RPiGpioBus()
    spi.open()
    gpio.open()
    return RPiHAL(spi=spi, gpio=gpio)
