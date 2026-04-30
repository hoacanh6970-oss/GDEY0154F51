from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MockSpiBus:
    writes: list[bytes] = field(default_factory=list)
    closed: bool = False

    def write(self, data: bytes) -> None:
        self.writes.append(bytes(data))

    def close(self) -> None:
        self.closed = True


@dataclass
class MockGpioBus:
    pin_mode: dict[int, str] = field(default_factory=dict)
    pin_values: dict[int, int] = field(default_factory=dict)
    writes: list[tuple[int, int]] = field(default_factory=list)
    cleaned: bool = False

    def setup_output(self, pin: int) -> None:
        self.pin_mode[pin] = "OUT"
        self.pin_values.setdefault(pin, 1)

    def setup_input(self, pin: int) -> None:
        self.pin_mode[pin] = "IN"
        self.pin_values.setdefault(pin, 1)

    def write(self, pin: int, value: int) -> None:
        self.pin_values[pin] = int(value)
        self.writes.append((pin, int(value)))

    def read(self, pin: int) -> int:
        return int(self.pin_values.get(pin, 1))

    def cleanup(self) -> None:
        self.cleaned = True

    def set_input_value(self, pin: int, value: int) -> None:
        self.pin_values[pin] = int(value)
