from __future__ import annotations

import base64
import io
import unittest

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    from fastapi.testclient import TestClient

    from gdey0154f51.mac_hub.app import create_app
    from gdey0154f51.mac_hub.config import MacHubConfig
    from gdey0154f51.mac_hub.service import MacHubService
    from gdey0154f51.pi_server.models import DisplayJobRequest

    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False


class _FakePiClient:
    def __init__(self) -> None:
        self._counter = 0
        self.submitted: list[DisplayJobRequest] = []

    async def submit_display_job(self, request: DisplayJobRequest) -> dict:
        self._counter += 1
        self.submitted.append(request)
        return {"job_id": f"pi-{self._counter}", "queue_position": 1}

    async def get_display_job(self, job_id: str) -> dict:
        return {
            "job_id": job_id,
            "status": "SUCCEEDED",
            "error": None,
            "queue_position": None,
            "created_at": "2026-01-01T00:00:00Z",
            "started_at": "2026-01-01T00:00:01Z",
            "finished_at": "2026-01-01T00:00:02Z",
        }


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed")
@unittest.skipIf(Image is None, "Pillow not installed")
class MacHubApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pi_client = _FakePiClient()
        self.service = MacHubService(pi_client=self.pi_client, prefer_native_buffer=True)
        self.app = create_app(
            config=MacHubConfig(
                bind_host="127.0.0.1",
                port=8780,
                pi_base_url="http://127.0.0.1:8765",
                pi_api_key="test-key",
                prefer_native_buffer=True,
            ),
            service=self.service,
        )

    def test_display_image_and_query_job(self) -> None:
        img_b64 = _sample_png_base64()
        with TestClient(self.app) as client:
            submit = client.post(
                "/api/v1/display/image",
                json={"image_base64": img_b64, "display_options": {"auto_sleep": True}},
            )
            self.assertEqual(submit.status_code, 202)
            body = submit.json()
            self.assertIn("job_id", body)
            self.assertTrue(body["pi_job_id"].startswith("pi-"))

            status = client.get(f"/api/v1/jobs/{body['job_id']}")
            self.assertEqual(status.status_code, 200)
            data = status.json()
            self.assertEqual(data["hub_status"], "FORWARDED")
            self.assertEqual(data["pi_status"], "SUCCEEDED")

            self.assertEqual(
                self.pi_client.submitted[-1].payload_format.value,
                "native_buffer_base64",
            )

    def test_text_and_todo_endpoints(self) -> None:
        with TestClient(self.app) as client:
            text_resp = client.post(
                "/api/v1/display/text",
                json={"text": "hello from mac hub", "title": "Note"},
            )
            self.assertEqual(text_resp.status_code, 202)

            todo_resp = client.post(
                "/api/v1/display/todo",
                json={"title": "Today", "items": [{"text": "ship", "done": False}]},
            )
            self.assertEqual(todo_resp.status_code, 202)

    def test_invalid_image_returns_400(self) -> None:
        with TestClient(self.app) as client:
            response = client.post(
                "/api/v1/display/image",
                json={"image_base64": "%%%"},
            )
            self.assertEqual(response.status_code, 400)

    def test_job_not_found(self) -> None:
        with TestClient(self.app) as client:
            response = client.get("/api/v1/jobs/missing")
            self.assertEqual(response.status_code, 404)


def _sample_png_base64() -> str:
    image = Image.new("RGB", (32, 32), (0, 0, 0))
    try:
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        return base64.b64encode(bio.getvalue()).decode("utf-8")
    finally:
        image.close()


if __name__ == "__main__":
    unittest.main()
