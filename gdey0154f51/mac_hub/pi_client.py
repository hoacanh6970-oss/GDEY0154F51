from __future__ import annotations

from typing import Any, Protocol

import httpx

from gdey0154f51.pi_server.models import DisplayJobRequest


class PiClient(Protocol):
    async def submit_display_job(self, request: DisplayJobRequest) -> dict[str, Any]: ...

    async def get_display_job(self, job_id: str) -> dict[str, Any]: ...


class HttpPiClient:
    def __init__(self, base_url: str, api_key: str, timeout_s: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_s = timeout_s

    async def submit_display_job(self, request: DisplayJobRequest) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            response = await client.post(
                f"{self._base_url}/v1/jobs/display",
                json=request.model_dump(mode="json"),
                headers={"X-API-Key": self._api_key},
            )
        if response.status_code != 202:
            raise RuntimeError(f"pi server returned {response.status_code}: {response.text}")
        return response.json()

    async def get_display_job(self, job_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            response = await client.get(
                f"{self._base_url}/v1/jobs/{job_id}",
                headers={"X-API-Key": self._api_key},
            )
        if response.status_code != 200:
            raise RuntimeError(f"pi server returned {response.status_code}: {response.text}")
        return response.json()
