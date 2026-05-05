from __future__ import annotations

import unittest

from gdey0154f51.constants import SpiConfig
from gdey0154f51.hal_rpi import RPiSpiBus


class _SpiWithWriteBytes2:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def writebytes2(self, data: bytes) -> None:
        self.calls.append(("writebytes2", bytes(data)))

    def xfer3(self, data: list[int]) -> list[int]:
        self.calls.append(("xfer3", list(data)))
        return data

    def xfer2(self, data: list[int]) -> list[int]:
        self.calls.append(("xfer2", list(data)))
        return data


class _SpiWithXfer3Only:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def xfer3(self, data: list[int]) -> list[int]:
        self.calls.append(("xfer3", list(data)))
        return data

    def xfer2(self, data: list[int]) -> list[int]:
        self.calls.append(("xfer2", list(data)))
        return data


class _SpiWithXfer2Only:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def xfer2(self, data: list[int]) -> list[int]:
        self.calls.append(("xfer2", list(data)))
        return data


class RPiSpiBusWriteTests(unittest.TestCase):
    def test_write_prefers_writebytes2_for_large_payloads(self) -> None:
        bus = RPiSpiBus(SpiConfig())
        spi = _SpiWithWriteBytes2()
        bus._spi = spi  # type: ignore[assignment]

        payload = bytes([0xAB]) * 10_000
        bus.write(payload)

        self.assertEqual(spi.calls, [("writebytes2", payload)])

    def test_write_falls_back_to_xfer3(self) -> None:
        bus = RPiSpiBus(SpiConfig())
        spi = _SpiWithXfer3Only()
        bus._spi = spi  # type: ignore[assignment]

        bus.write(b"\x10\x20")
        self.assertEqual(spi.calls, [("xfer3", [0x10, 0x20])])

    def test_write_falls_back_to_xfer2(self) -> None:
        bus = RPiSpiBus(SpiConfig())
        spi = _SpiWithXfer2Only()
        bus._spi = spi  # type: ignore[assignment]

        bus.write(b"\x01\x02\x03")
        self.assertEqual(spi.calls, [("xfer2", [0x01, 0x02, 0x03])])


if __name__ == "__main__":
    unittest.main()
