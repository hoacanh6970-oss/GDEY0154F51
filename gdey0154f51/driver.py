from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .constants import (
    BUFFER_SIZE,
    DEMO_TO_NATIVE_2BIT,
    FILL_BYTE_BY_COLOR,
    Color,
    PinConfig,
    SpiConfig,
)
from .hal_rpi import create_rpi_hal
from .image_converter import ConvertOptions, ImageConverter
from .interfaces import GpioBus, SpiBus


@dataclass
class DriverTrace:
    kind: str
    value: int


class GDEY0154F51Controller:
    """Low-level controller that matches the Arduino command sequence."""

    def __init__(
        self,
        spi: SpiBus,
        gpio: GpioBus,
        pins: PinConfig | None = None,
        busy_timeout_s: float = 20.0,
        busy_poll_interval_s: float = 0.01,
        sleep_fn=time.sleep,
    ) -> None:
        self.spi = spi
        self.gpio = gpio
        self.pins = pins or PinConfig()
        self.busy_timeout_s = busy_timeout_s
        self.busy_poll_interval_s = busy_poll_interval_s
        self.sleep_fn = sleep_fn
        self.trace: list[DriverTrace] = []
        self.last_ram: bytes = b""

        self._setup_pins()

    def _setup_pins(self) -> None:
        self.gpio.setup_input(self.pins.busy)
        self.gpio.setup_output(self.pins.rst)
        self.gpio.setup_output(self.pins.dc)
        self.gpio.setup_output(self.pins.cs)
        self.gpio.write(self.pins.cs, 1)
        self.gpio.write(self.pins.rst, 1)

    def write_command(self, command: int) -> None:
        self.gpio.write(self.pins.cs, 0)
        self.gpio.write(self.pins.dc, 0)
        self.spi.write(bytes([command & 0xFF]))
        self.gpio.write(self.pins.cs, 1)
        self.trace.append(DriverTrace("cmd", command & 0xFF))

    def write_data_byte(self, value: int) -> None:
        self.gpio.write(self.pins.cs, 0)
        self.gpio.write(self.pins.dc, 1)
        self.spi.write(bytes([value & 0xFF]))
        self.gpio.write(self.pins.cs, 1)
        self.trace.append(DriverTrace("data", value & 0xFF))

    def write_data(self, data: bytes) -> None:
        for value in data:
            self.write_data_byte(value)

    def wait_until_idle(self, timeout_s: float | None = None) -> None:
        timeout = self.busy_timeout_s if timeout_s is None else timeout_s
        deadline = time.monotonic() + timeout

        while self.gpio.read(self.pins.busy) != 1:
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"BUSY pin did not become ready within {timeout:.2f}s"
                )
            self.sleep_fn(self.busy_poll_interval_s)

    def hardware_reset(self) -> None:
        self.sleep_fn(0.02)
        self.gpio.write(self.pins.rst, 0)
        self.sleep_fn(0.04)
        self.gpio.write(self.pins.rst, 1)
        self.sleep_fn(0.05)

    def init_full_update(self) -> None:
        self.hardware_reset()
        self.wait_until_idle()

        self.write_command(0x4D)
        self.write_data_byte(0x78)

        self.write_command(0x00)
        self.write_data(bytes([0x0F, 0x29]))

        self.write_command(0x01)
        self.write_data(bytes([0x07, 0x00]))

        self.write_command(0x03)
        self.write_data(bytes([0x10, 0x54, 0x44]))

        self.write_command(0x06)
        self.write_data(bytes([0x05, 0x00, 0x3F, 0x0A, 0x25, 0x12, 0x1A]))

        self.write_command(0x50)
        self.write_data_byte(0x37)

        self.write_command(0x60)
        self.write_data(bytes([0x02, 0x02]))

        self.write_command(0x61)
        self.write_data(bytes([0x00, 0x98, 0x00, 0x98]))

        self.write_command(0xE7)
        self.write_data_byte(0x1C)

        self.write_command(0xE3)
        self.write_data_byte(0x22)

        self.write_command(0xB4)
        self.write_data_byte(0xD0)

        self.write_command(0xB5)
        self.write_data_byte(0x03)

        self.write_command(0xE9)
        self.write_data_byte(0x01)

        self.write_command(0x30)
        self.write_data_byte(0x08)

        self.write_command(0x04)
        self.wait_until_idle()

    def write_ram(self, buffer: bytes) -> None:
        if len(buffer) != BUFFER_SIZE:
            raise ValueError(f"buffer size must be {BUFFER_SIZE} bytes")
        self.write_command(0x10)
        self.write_data(buffer)
        self.last_ram = bytes(buffer)

    def refresh(self) -> None:
        self.write_command(0x12)
        self.write_data_byte(0x00)
        self.wait_until_idle()

    def sleep(self) -> None:
        self.write_command(0x02)
        self.wait_until_idle()
        self.sleep_fn(0.1)

        self.write_command(0x07)
        self.write_data_byte(0xA5)


class GDEY0154F51:
    """High-level display API for Raspberry Pi usage."""

    def __init__(
        self,
        controller: GDEY0154F51Controller,
        image_converter: ImageConverter | None = None,
    ) -> None:
        self.controller = controller
        self.converter = image_converter or ImageConverter()

    @classmethod
    def from_rpi(
        cls,
        pin_config: PinConfig | None = None,
        spi_config: SpiConfig | None = None,
        busy_timeout_s: float = 20.0,
    ) -> "GDEY0154F51":
        hal = create_rpi_hal(pin_config=pin_config, spi_config=spi_config)
        controller = GDEY0154F51Controller(
            spi=hal.spi,
            gpio=hal.gpio,
            pins=pin_config or PinConfig(),
            busy_timeout_s=busy_timeout_s,
        )
        return cls(controller=controller)

    def display_native_buffer(self, buffer: bytes, auto_sleep: bool = True) -> None:
        self.controller.init_full_update()
        self.controller.write_ram(buffer)
        self.controller.refresh()
        if auto_sleep:
            self.controller.sleep()

    def display_demo_buffer(self, demo_buffer: bytes, auto_sleep: bool = True) -> None:
        if len(demo_buffer) != BUFFER_SIZE:
            raise ValueError(f"buffer size must be {BUFFER_SIZE} bytes")

        native = bytearray(BUFFER_SIZE)
        for i, value in enumerate(demo_buffer):
            p0 = DEMO_TO_NATIVE_2BIT[(value >> 6) & 0x03]
            p1 = DEMO_TO_NATIVE_2BIT[(value >> 4) & 0x03]
            p2 = DEMO_TO_NATIVE_2BIT[(value >> 2) & 0x03]
            p3 = DEMO_TO_NATIVE_2BIT[value & 0x03]
            native[i] = (p0 << 6) | (p1 << 4) | (p2 << 2) | p3

        self.display_native_buffer(bytes(native), auto_sleep=auto_sleep)

    def display_image(
        self,
        image_path: str | Path,
        dither: bool = True,
        fit: str = "contain",
        rotate: int = 0,
        auto_sleep: bool = True,
    ) -> None:
        options = ConvertOptions(dither=dither, fit=fit, rotate=rotate)
        buffer = self.converter.convert_file(image_path, options=options)
        self.display_native_buffer(buffer, auto_sleep=auto_sleep)

    def fill(self, color: Color, auto_sleep: bool = True) -> None:
        fill_byte = FILL_BYTE_BY_COLOR[color]
        buffer = bytes([fill_byte]) * BUFFER_SIZE
        self.display_native_buffer(buffer, auto_sleep=auto_sleep)

    def clear(self, auto_sleep: bool = True) -> None:
        self.fill(Color.WHITE, auto_sleep=auto_sleep)

    def close(self) -> None:
        try:
            self.controller.spi.close()
        finally:
            self.controller.gpio.cleanup()

    def __enter__(self) -> "GDEY0154F51":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
