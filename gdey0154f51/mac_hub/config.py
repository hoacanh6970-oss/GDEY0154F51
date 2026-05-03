from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    return lowered in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MacHubConfig:
    bind_host: str
    port: int
    pi_base_url: str
    pi_api_key: str
    prefer_native_buffer: bool

    @classmethod
    def from_env(cls) -> "MacHubConfig":
        return cls(
            bind_host=os.getenv("HUB_BIND_HOST", "127.0.0.1"),
            port=_get_int("HUB_PORT", 8780),
            pi_base_url=os.getenv("PI_BASE_URL", "http://127.0.0.1:8765").rstrip("/"),
            pi_api_key=os.getenv("PI_API_KEY", "dev-api-key"),
            prefer_native_buffer=_get_bool("PREFER_NATIVE_BUFFER", True),
        )
