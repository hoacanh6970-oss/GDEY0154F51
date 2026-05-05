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
        manual_cs: bool = False,
        busy_ready_level: int = 1,
        busy_auto_fallback: bool = False,
        initial_busy_timeout_s: float = 0.25,
        busy_timeout_s: float = 20.0,
        busy_poll_interval_s: float = 0.01,
        sleep_fn=time.sleep,
    ) -> None:
        self.spi = spi
        self.gpio = gpio
        self.pins = pins or PinConfig()
        self.manual_cs = manual_cs
        self.busy_ready_level = 1 if busy_ready_level else 0
        self.busy_auto_fallback = busy_auto_fallback
        self._busy_fallback_used = False
        self.initial_busy_timeout_s = initial_busy_timeout_s
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
        if self.manual_cs:
            self.gpio.setup_output(self.pins.cs)
            self.gpio.write(self.pins.cs, 1)
        self.gpio.write(self.pins.rst, 1)

    def _select_chip(self) -> None:
        if self.manual_cs:
            self.gpio.write(self.pins.cs, 0)

    def _deselect_chip(self) -> None:
        if self.manual_cs:
            self.gpio.write(self.pins.cs, 1)

    def write_command(self, command: int) -> None:
        self._select_chip()
        self.gpio.write(self.pins.dc, 0)
        self.spi.write(bytes([command & 0xFF]))
        self._deselect_chip()
        self.trace.append(DriverTrace("cmd", command & 0xFF))

    def write_data_byte(self, value: int) -> None:
        self._write_data_payload(bytes([value & 0xFF]))

    def write_data(self, data: bytes) -> None:
        payload = bytes(data)
        self._write_data_payload(payload)

    def _write_data_payload(self, payload: bytes) -> None:
        if not payload:
            return
        self.gpio.write(self.pins.dc, 1)
        self._select_chip()
        self.spi.write(payload)
        self._deselect_chip()
        for value in payload:
            self.trace.append(DriverTrace("data", value))

    def _wait_until_busy_level(self, ready_level: int, timeout_s: float) -> None:
        deadline = time.monotonic() + timeout_s

        while self.gpio.read(self.pins.busy) != ready_level:
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"BUSY pin did not become ready within {timeout_s:.2f}s"
                )
            self.sleep_fn(self.busy_poll_interval_s)

    def wait_until_idle(self, timeout_s: float | None = None) -> None:
        timeout = self.busy_timeout_s if timeout_s is None else timeout_s
        try:
            self._wait_until_busy_level(self.busy_ready_level, timeout)
            return
        except TimeoutError:
            # Some board revisions expose inverse BUSY polarity.
            if not self.busy_auto_fallback or self._busy_fallback_used:
                raise

        opposite_level = 1 - self.busy_ready_level
        self._wait_until_busy_level(opposite_level, timeout)
        self.busy_ready_level = opposite_level
        self._busy_fallback_used = True

    def hardware_reset(self) -> None:
        self.sleep_fn(0.02)
        self.gpio.write(self.pins.rst, 0)
        self.sleep_fn(0.04)
        self.gpio.write(self.pins.rst, 1)
        self.sleep_fn(0.05)

    def wait_until_idle_after_reset(self) -> None:
        # Some boards keep BUSY asserted until the first init/power-on command
        # after deep sleep. Treat this pre-init wait as a best-effort probe.
        self.wait_until_idle(timeout_s=self.initial_busy_timeout_s)

    def init_full_update(self) -> None:
        self.hardware_reset()
        try:
            self.wait_until_idle_after_reset()
        except TimeoutError:
            pass

        self.write_command(0x4D)
        self.write_data_byte(0x78)

        self.write_command(0x00)
        self.write_data(bytes([0x0F, 0x29]))

        self.write_command(0x06)
        self.write_data(bytes([0x0D, 0x12, 0x30, 0x20, 0x19, 0x2A, 0x22]))

        self.write_command(0x50)
        self.write_data_byte(0x37)

        self.write_command(0x61)
        self.write_data(bytes([0x00, 0xC8, 0x00, 0xC8]))

        self.write_command(0xE9)
        self.write_data_byte(0x01)

        self.write_command(0x30)
        self.write_data_byte(0x08)

        self.write_command(0x04)
        self.wait_until_idle()

    def init_fast_update(self) -> None:
        self.init_full_update()

        self.write_command(0xE0)
        self.write_data_byte(0x02)

        self.write_command(0xE6)
        self.write_data_byte(0x5D)

        self.write_command(0xA5)
        self.write_data_byte(0x00)
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
        self.write_data_byte(0x00)
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
        busy_ready_level: int = 1,
        busy_auto_fallback: bool = True,
        busy_timeout_s: float = 20.0,
    ) -> "GDEY0154F51":
        effective_spi_config = spi_config or SpiConfig()
        hal = create_rpi_hal(pin_config=pin_config, spi_config=effective_spi_config)
        controller = GDEY0154F51Controller(
            spi=hal.spi,
            gpio=hal.gpio,
            pins=pin_config or PinConfig(),
            manual_cs=not effective_spi_config.use_hardware_cs,
            busy_ready_level=busy_ready_level,
            busy_auto_fallback=busy_auto_fallback,
            busy_timeout_s=busy_timeout_s,
        )
        return cls(controller=controller)

    def display_native_buffer(
        self, buffer: bytes, auto_sleep: bool = True, fast_update: bool = False
    ) -> None:
        if fast_update:
            self.controller.init_fast_update()
        else:
            self.controller.init_full_update()
        self.controller.write_ram(buffer)
        self.controller.refresh()
        if auto_sleep:
            self.controller.sleep()

    def display_demo_buffer(
        self, demo_buffer: bytes, auto_sleep: bool = True, fast_update: bool = False
    ) -> None:
        if len(demo_buffer) != BUFFER_SIZE:
            raise ValueError(f"buffer size must be {BUFFER_SIZE} bytes")

        native = bytearray(BUFFER_SIZE)
        for i, value in enumerate(demo_buffer):
            p0 = DEMO_TO_NATIVE_2BIT[(value >> 6) & 0x03]
            p1 = DEMO_TO_NATIVE_2BIT[(value >> 4) & 0x03]
            p2 = DEMO_TO_NATIVE_2BIT[(value >> 2) & 0x03]
            p3 = DEMO_TO_NATIVE_2BIT[value & 0x03]
            native[i] = (p0 << 6) | (p1 << 4) | (p2 << 2) | p3

        self.display_native_buffer(
            bytes(native), auto_sleep=auto_sleep, fast_update=fast_update
        )

    def display_image(
        self,
        image_path: str | Path,
        dither: bool = True,
        fit: str = "contain",
        rotate: int = 0,
        auto_sleep: bool = True,
        fast_update: bool = False,
    ) -> None:
        options = ConvertOptions(dither=dither, fit=fit, rotate=rotate)
        buffer = self.converter.convert_file(image_path, options=options)
        self.display_native_buffer(
            buffer, auto_sleep=auto_sleep, fast_update=fast_update
        )

    def fill(
        self, color: Color, auto_sleep: bool = True, fast_update: bool = False
    ) -> None:
        fill_byte = FILL_BYTE_BY_COLOR[color]
        buffer = bytes([fill_byte]) * BUFFER_SIZE
        self.display_native_buffer(
            buffer, auto_sleep=auto_sleep, fast_update=fast_update
        )

    def clear(self, auto_sleep: bool = True, fast_update: bool = False) -> None:
        self.fill(Color.WHITE, auto_sleep=auto_sleep, fast_update=fast_update)

    def close(self) -> None:
        try:
            self.controller.spi.close()
        finally:
            self.controller.gpio.cleanup()

    def __enter__(self) -> "GDEY0154F51":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
