from __future__ import annotations

import base64
import time
import unittest

from gdey0154f51.constants import BUFFER_SIZE
from gdey0154f51.constants import PinConfig, SpiConfig

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    from fastapi.testclient import TestClient

    from gdey0154f51.pi_server.app import create_app
    from gdey0154f51.pi_server.config import PiServerConfig
    from gdey0154f51.pi_server.service import PiDisplayService

    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False


class _FakeDisplayDevice:
    def __init__(self, sink: list[tuple[int, bool]], delay_s: float = 0.0) -> None:
        self._sink = sink
        self._delay_s = delay_s

    def display_native_buffer(self, buffer: bytes, auto_sleep: bool = True) -> None:
        self._sink.append((len(buffer), auto_sleep))
        if self._delay_s:
            time.sleep(self._delay_s)

    def close(self) -> None:
        return None


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed")
class PiServerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key = "test-key"
        self.display_calls: list[tuple[int, bool]] = []
        self.service = PiDisplayService(
            device_factory=lambda: _FakeDisplayDevice(self.display_calls, delay_s=0.1),
            queue_max_size=1,
        )
        self.app = create_app(
            config=PiServerConfig(
                api_key=self.api_key,
                bind_host="127.0.0.1",
                port=8765,
                queue_max_size=1,
                busy_timeout_s=1.0,
                pin_config=PinConfig(),
                spi_config=SpiConfig(),
            ),
            service=self.service,
        )

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key}

    def test_health_and_capabilities(self) -> None:
        with TestClient(self.app) as client:
            health = client.get("/v1/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["ok"], True)

            caps = client.get("/v1/capabilities")
            self.assertEqual(caps.status_code, 200)
            self.assertEqual(caps.json()["buffer_size"], BUFFER_SIZE)

    def test_requires_api_key(self) -> None:
        with TestClient(self.app) as client:
            response = client.post(
                "/v1/jobs/display",
                json={
                    "payload_format": "native_buffer_base64",
                    "payload_data": base64.b64encode(bytes([0x55]) * BUFFER_SIZE).decode("utf-8"),
                },
            )
            self.assertEqual(response.status_code, 401)

    def test_native_buffer_size_validation(self) -> None:
        with TestClient(self.app) as client:
            response = client.post(
                "/v1/jobs/display",
                headers=self._headers(),
                json={
                    "payload_format": "native_buffer_base64",
                    "payload_data": base64.b64encode(b"short").decode("utf-8"),
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_invalid_base64_validation(self) -> None:
        with TestClient(self.app) as client:
            response = client.post(
                "/v1/jobs/display",
                headers=self._headers(),
                json={
                    "payload_format": "native_buffer_base64",
                    "payload_data": "%%%",
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_queue_status_progression(self) -> None:
        payload = base64.b64encode(bytes([0x55]) * BUFFER_SIZE).decode("utf-8")
        with TestClient(self.app) as client:
            submit = client.post(
                "/v1/jobs/display",
                headers=self._headers(),
                json={"payload_format": "native_buffer_base64", "payload_data": payload},
            )
            self.assertEqual(submit.status_code, 202)
            job_id = submit.json()["job_id"]

            initial = client.get(f"/v1/jobs/{job_id}", headers=self._headers())
            self.assertEqual(initial.status_code, 200)
            self.assertIn(initial.json()["status"], {"QUEUED", "RUNNING"})

            final = self._wait_for_done(client, job_id)
            self.assertEqual(final["status"], "SUCCEEDED")
            self.assertEqual(self.display_calls[-1][0], BUFFER_SIZE)

    @unittest.skipIf(Image is None, "Pillow not installed")
    def test_image_payload_supported(self) -> None:
        image = Image.new("RGB", (40, 40), (220, 0, 0))
        try:
            import io

            out = io.BytesIO()
            image.save(out, format="PNG")
            b64 = base64.b64encode(out.getvalue()).decode("utf-8")
        finally:
            image.close()

        with TestClient(self.app) as client:
            submit = client.post(
                "/v1/jobs/display",
                headers=self._headers(),
                json={
                    "payload_format": "image_base64",
                    "payload_data": b64,
                    "display_options": {"fit": "contain", "rotate": 0, "dither": True, "auto_sleep": True},
                },
            )
            self.assertEqual(submit.status_code, 202)
            job_id = submit.json()["job_id"]
            final = self._wait_for_done(client, job_id)
            self.assertEqual(final["status"], "SUCCEEDED")

    def test_queue_full_returns_429(self) -> None:
        payload = base64.b64encode(bytes([0x55]) * BUFFER_SIZE).decode("utf-8")
        saw_429 = False
        with TestClient(self.app) as client:
            for _ in range(20):
                resp = client.post(
                    "/v1/jobs/display",
                    headers=self._headers(),
                    json={"payload_format": "native_buffer_base64", "payload_data": payload},
                )
                if resp.status_code == 429:
                    saw_429 = True
                    break
            self.assertTrue(saw_429)

    def _wait_for_done(self, client: TestClient, job_id: str, timeout_s: float = 3.0) -> dict:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            response = client.get(f"/v1/jobs/{job_id}", headers=self._headers())
            self.assertEqual(response.status_code, 200)
            data = response.json()
            if data["status"] in {"SUCCEEDED", "FAILED"}:
                return data
            time.sleep(0.05)
        raise AssertionError("job did not finish in time")


if __name__ == "__main__":
    unittest.main()
