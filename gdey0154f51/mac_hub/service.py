from __future__ import annotations

import base64
import binascii
import io
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from gdey0154f51.image_converter import ConvertOptions, ImageConverter
from gdey0154f51.mac_hub.models import (
    DisplayImageRequest,
    DisplayTextRequest,
    DisplayTodoRequest,
    HubJobAccepted,
    HubJobState,
    HubJobStatusResponse,
)
from gdey0154f51.mac_hub.pi_client import PiClient
from gdey0154f51.mac_hub.renderer import render_text_image, render_todo_image
from gdey0154f51.pi_server.models import ContentMeta, DisplayJobRequest, PayloadFormat


@dataclass
class HubJobRecord:
    hub_status: HubJobState
    pi_job_id: str | None
    created_at: datetime
    updated_at: datetime
    pi_status: str | None = None
    pi_error: str | None = None
    forward_error: str | None = None


class MacHubService:
    def __init__(
        self,
        pi_client: PiClient,
        image_converter: ImageConverter | None = None,
        prefer_native_buffer: bool = True,
    ) -> None:
        self._pi_client = pi_client
        self._converter = image_converter or ImageConverter()
        self._prefer_native_buffer = prefer_native_buffer
        self._jobs: dict[str, HubJobRecord] = {}
        self._lock = threading.Lock()

    async def submit_image(self, request: DisplayImageRequest) -> HubJobAccepted:
        payload = await self._build_payload_for_image(request)
        return await self._forward(payload)

    async def submit_text(self, request: DisplayTextRequest) -> HubJobAccepted:
        image = render_text_image(request.text, title=request.title)
        try:
            payload = self._build_payload_from_pil(
                image=image,
                display_options=request.display_options,
                source=request.source,
                client_job_id=request.client_job_id,
            )
        finally:
            image.close()
        return await self._forward(payload)

    async def submit_todo(self, request: DisplayTodoRequest) -> HubJobAccepted:
        image = render_todo_image(
            title=request.title,
            items=[(item.text, item.done) for item in request.items],
        )
        try:
            payload = self._build_payload_from_pil(
                image=image,
                display_options=request.display_options,
                source=request.source,
                client_job_id=request.client_job_id,
            )
        finally:
            image.close()
        return await self._forward(payload)

    async def get_job(self, hub_job_id: str) -> HubJobStatusResponse | None:
        with self._lock:
            record = self._jobs.get(hub_job_id)
            if record is None:
                return None

        if record.pi_job_id:
            try:
                pi_job = await self._pi_client.get_display_job(record.pi_job_id)
                with self._lock:
                    latest = self._jobs[hub_job_id]
                    latest.hub_status = HubJobState.FORWARDED
                    latest.pi_status = pi_job.get("status")
                    latest.pi_error = pi_job.get("error")
                    latest.updated_at = datetime.now(timezone.utc)
                    record = latest
            except Exception as exc:
                with self._lock:
                    latest = self._jobs[hub_job_id]
                    latest.forward_error = str(exc)
                    latest.updated_at = datetime.now(timezone.utc)
                    record = latest

        return HubJobStatusResponse(
            job_id=hub_job_id,
            pi_job_id=record.pi_job_id,
            hub_status=record.hub_status,
            pi_status=record.pi_status,
            pi_error=record.pi_error,
            created_at=record.created_at,
            updated_at=record.updated_at,
            forward_error=record.forward_error,
        )

    async def _build_payload_for_image(self, request: DisplayImageRequest) -> DisplayJobRequest:
        content_meta = ContentMeta(
            mime_type=request.mime_type,
            source=request.source,
            client_job_id=request.client_job_id,
        )

        if not self._prefer_native_buffer:
            return DisplayJobRequest(
                payload_format=PayloadFormat.IMAGE_BASE64,
                payload_data=request.image_base64,
                display_options=request.display_options,
                content_meta=content_meta,
            )

        raw = _decode_base64(request.image_base64)
        image = _open_image(raw)
        try:
            options = ConvertOptions(
                dither=request.display_options.dither,
                fit=request.display_options.fit,
                rotate=request.display_options.rotate,
            )
            native = self._converter.convert_image(image, options=options)
        finally:
            image.close()

        return DisplayJobRequest(
            payload_format=PayloadFormat.NATIVE_BUFFER_BASE64,
            payload_data=base64.b64encode(native).decode("utf-8"),
            display_options=request.display_options,
            content_meta=content_meta,
        )

    def _build_payload_from_pil(
        self,
        image,
        display_options,
        source: str | None,
        client_job_id: str | None,
    ) -> DisplayJobRequest:
        options = ConvertOptions(
            dither=display_options.dither,
            fit=display_options.fit,
            rotate=display_options.rotate,
        )
        native = self._converter.convert_image(image, options=options)
        return DisplayJobRequest(
            payload_format=PayloadFormat.NATIVE_BUFFER_BASE64,
            payload_data=base64.b64encode(native).decode("utf-8"),
            content_meta=ContentMeta(
                mime_type="image/native-buffer",
                source=source,
                client_job_id=client_job_id,
            ),
            display_options=display_options,
        )

    async def _forward(self, payload: DisplayJobRequest) -> HubJobAccepted:
        hub_job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        with self._lock:
            self._jobs[hub_job_id] = HubJobRecord(
                hub_status=HubJobState.ACCEPTED,
                pi_job_id=None,
                created_at=now,
                updated_at=now,
            )

        try:
            response = await self._pi_client.submit_display_job(payload)
            pi_job_id = response["job_id"]
            with self._lock:
                record = self._jobs[hub_job_id]
                record.pi_job_id = pi_job_id
                record.hub_status = HubJobState.FORWARDED
                record.updated_at = datetime.now(timezone.utc)
            return HubJobAccepted(job_id=hub_job_id, pi_job_id=pi_job_id)
        except Exception as exc:
            with self._lock:
                record = self._jobs[hub_job_id]
                record.hub_status = HubJobState.FAILED_TO_FORWARD
                record.forward_error = str(exc)
                record.updated_at = datetime.now(timezone.utc)
            raise


def _decode_base64(payload: str) -> bytes:
    try:
        return base64.b64decode(payload.encode("utf-8"), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("image_base64 is not valid base64") from exc


def _open_image(raw: bytes):
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(raw))
        image.load()
        return image
    except Exception as exc:
        raise ValueError("image_base64 is not a valid image") from exc
