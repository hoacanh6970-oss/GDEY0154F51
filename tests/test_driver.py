from __future__ import annotations

import unittest

from gdey0154f51.constants import BUFFER_SIZE, Color, PinConfig
from gdey0154f51.driver import GDEY0154F51, GDEY0154F51Controller
from gdey0154f51.mock_hal import MockGpioBus, MockSpiBus


class DriverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spi = MockSpiBus()
        self.gpio = MockGpioBus()
        self.pins = PinConfig(rst=17, dc=25, cs=8, busy=24)
        self.controller = GDEY0154F51Controller(
            spi=self.spi,
            gpio=self.gpio,
            pins=self.pins,
            busy_timeout_s=0.05,
            busy_poll_interval_s=0.001,
            sleep_fn=lambda _: None,
        )
        self.device = GDEY0154F51(controller=self.controller)

    def test_init_sequence_contains_expected_command_order(self) -> None:
        self.gpio.set_input_value(self.pins.busy, 1)
        self.controller.init_full_update()

        commands = [item.value for item in self.controller.trace if item.kind == "cmd"]
        self.assertEqual(
            commands,
            [
                0x4D,
                0x00,
                0x01,
                0x03,
                0x06,
                0x50,
                0x60,
                0x61,
                0xE7,
                0xE3,
                0xB4,
                0xB5,
                0xE9,
                0x30,
                0x04,
            ],
        )

    def test_wait_busy_timeout(self) -> None:
        self.gpio.set_input_value(self.pins.busy, 0)
        with self.assertRaises(TimeoutError):
            self.controller.wait_until_idle(timeout_s=0.01)

    def test_fill_white_generates_expected_native_buffer(self) -> None:
        self.gpio.set_input_value(self.pins.busy, 1)
        self.device.fill(Color.WHITE, auto_sleep=False)

        self.assertEqual(len(self.controller.last_ram), BUFFER_SIZE)
        self.assertTrue(all(value == 0x55 for value in self.controller.last_ram))

    def test_demo_buffer_remap(self) -> None:
        self.gpio.set_input_value(self.pins.busy, 1)
        # demo order byte: 00 01 10 11 => native order: 01 10 11 00 (0x6C)
        demo = bytes([0x1B]) * BUFFER_SIZE
        self.device.display_demo_buffer(demo, auto_sleep=False)

        self.assertEqual(self.controller.last_ram[0], 0x6C)

    def test_hardware_cs_mode_does_not_allocate_cs_gpio(self) -> None:
        self.assertNotIn(self.pins.cs, self.gpio.pin_mode)

    def test_init_continues_when_busy_stays_low_after_reset(self) -> None:
        reads = {"count": 0}

        def dynamic_read(pin: int) -> int:
            if pin != self.pins.busy:
                return self.gpio.pin_values.get(pin, 1)
            reads["count"] += 1
            if reads["count"] < 300:
                return 0
            return 1

        self.gpio.read = dynamic_read  # type: ignore[method-assign]
        self.controller.init_full_update()

        commands = [item.value for item in self.controller.trace if item.kind == "cmd"]
        self.assertIn(0x04, commands)


if __name__ == "__main__":
    unittest.main()
