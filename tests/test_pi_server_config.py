from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from gdey0154f51.pi_server.config import PiServerConfig


class PiServerConfigTests(unittest.TestCase):
    def test_reads_soft_spi_env_overrides(self) -> None:
        env = {
            "SPI_BACKEND": "software",
            "SOFT_SPI_SCK_PIN": "21",
            "SOFT_SPI_MOSI_PIN": "20",
            "SOFT_SPI_BIT_DELAY_US": "3",
            "SOFT_SPI_CS_GAP_US": "12",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = PiServerConfig.from_env()

        self.assertEqual(cfg.spi_config.backend, "software")
        self.assertEqual(cfg.spi_config.soft_sck_pin, 21)
        self.assertEqual(cfg.spi_config.soft_mosi_pin, 20)
        self.assertEqual(cfg.spi_config.soft_bit_delay_us, 3)
        self.assertEqual(cfg.spi_config.soft_cs_gap_us, 12)


if __name__ == "__main__":
    unittest.main()
