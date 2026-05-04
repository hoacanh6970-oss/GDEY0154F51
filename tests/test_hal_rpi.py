from __future__ import annotations

import unittest
from unittest.mock import patch

from gdey0154f51.constants import SpiConfig
from gdey0154f51.hal_rpi import RPiSoftSpiBus, create_rpi_hal
from gdey0154f51.mock_hal import MockGpioBus


class SoftSpiTests(unittest.TestCase):
    def test_soft_spi_writes_msb_first_with_expected_clock_edges(self) -> None:
        gpio = MockGpioBus()
        delay_calls: list[float] = []
        spi = RPiSoftSpiBus(
            gpio=gpio,
            config=SpiConfig(
                backend="software",
                soft_sck_pin=11,
                soft_mosi_pin=10,
                soft_bit_delay_us=1,
            ),
            sleep_fn=delay_calls.append,
        )

        spi.open()
        spi.write(bytes([0xA5]))

        writes = gpio.writes[2:]
        expected = []
        for bit in [1, 0, 1, 0, 0, 1, 0, 1]:
            expected.extend([(10, bit), (11, 1), (11, 0)])
        self.assertEqual(writes, expected)
        self.assertEqual(len(delay_calls), 16)

    def test_soft_spi_rejects_non_mode0(self) -> None:
        gpio = MockGpioBus()
        spi = RPiSoftSpiBus(gpio=gpio, config=SpiConfig(backend="software", mode=1))
        with self.assertRaises(ValueError):
            spi.open()


class HalSelectionTests(unittest.TestCase):
    def test_create_rpi_hal_uses_software_spi_backend_without_spidev(self) -> None:
        with patch("gdey0154f51.hal_rpi.RPiGpioBus.open", return_value=None), patch(
            "gdey0154f51.hal_rpi.RPiSoftSpiBus.open", return_value=None
        ):
            hal = create_rpi_hal(spi_config=SpiConfig(backend="software"))
        self.assertIsInstance(hal.spi, RPiSoftSpiBus)

    def test_create_rpi_hal_hardware_backend_still_uses_hardware_bus(self) -> None:
        with patch("gdey0154f51.hal_rpi.RPiGpioBus.open", return_value=None), patch(
            "gdey0154f51.hal_rpi.RPiSpiBus.open", return_value=None
        ):
            hal = create_rpi_hal(spi_config=SpiConfig(backend="hardware"))
        self.assertEqual(hal.spi.__class__.__name__, "RPiSpiBus")


if __name__ == "__main__":
    unittest.main()
