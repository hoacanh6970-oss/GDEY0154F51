from __future__ import annotations

import base64
import binascii
import io
import queue
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from gdey0154f51.constants import BUFFER_SIZE
from gdey0154f51.image_converter import ConvertOptions, ImageConverter
from gdey0154f51.pi_server.models import (
    DisplayJobRequest,
    DisplayJobStatusResponse,
    JobStatus,
    PayloadFormat,
)


class DisplayDevice(Protocol):
    def display_native_buffer(self, buffer: bytes, auto_sleep: bool = True) -> None: ...

    def close(self) -> None: ...


class DisplayDeviceFactory(Protocol):
    def __call__(self) -> DisplayDevice: ...


class QueueFullError(RuntimeError):
    pass


class InvalidRequestError(ValueError):
    pass


@dataclass
class JobRecord:
    request: DisplayJobRequest
    status: JobStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class PiDisplayService:
    def __init__(
        self,
        device_factory: DisplayDeviceFactory,
        queue_max_size: int = 100,
        image_converter: ImageConverter | None = None,
    ) -> None:
        self._device_factory = device_factory
        self._queue: queue.Queue[str] = queue.Queue(maxsize=queue_max_size)
        self._converter = image_converter or ImageConverter()

        self._jobs: dict[str, JobRecord] = {}
        self._jobs_lock = threading.Lock()

        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._run_worker, name="pi-display-worker")
        self._worker.daemon = True
        self._worker.start()

    def stop(self, timeout_s: float = 2.0) -> None:
        self._stop_event.set()
        if self._worker is not None:
            self._worker.join(timeout=timeout_s)

    def submit_job(self, request: DisplayJobRequest) -> tuple[str, int]:
        self._validate_request(request)

        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        record = JobRecord(request=request, status=JobStatus.QUEUED, created_at=now)

        with self._jobs_lock:
            self._jobs[job_id] = record

        try:
            self._queue.put_nowait(job_id)
        except queue.Full:
            with self._jobs_lock:
                self._jobs.pop(job_id, None)
            raise QueueFullError("display queue is full")

        queue_position = max(1, self._queue.qsize())
        return job_id, queue_position

    def get_job(self, job_id: str) -> DisplayJobStatusResponse | None:
        with self._jobs_lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            queue_position = self._queue_position_for(job_id) if record.status == JobStatus.QUEUED else None
            return DisplayJobStatusResponse(
                job_id=job_id,
                status=record.status,
                error=record.error,
                queue_position=queue_position,
                created_at=record.created_at,
                started_at=record.started_at,
                finished_at=record.finished_at,
            )

    def _run_worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                job_id = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            self._mark_running(job_id)
            try:
                with _DeviceSession(self._device_factory) as device:
                    buffer, auto_sleep = self._prepare_buffer_and_mode(job_id)
                    device.display_native_buffer(buffer, auto_sleep=auto_sleep)
                self._mark_succeeded(job_id)
            except Exception as exc:  # pragma: no cover - still covered via api tests
                self._mark_failed(job_id, str(exc))
            finally:
                self._queue.task_done()

    def _prepare_buffer_and_mode(self, job_id: str) -> tuple[bytes, bool]:
        with self._jobs_lock:
            record = self._jobs[job_id]
            request = record.request

        raw = _decode_base64_payload(request.payload_data)
        auto_sleep = request.display_options.auto_sleep

        if request.payload_format == PayloadFormat.NATIVE_BUFFER_BASE64:
            if len(raw) != BUFFER_SIZE:
                raise InvalidRequestError(
                    f"native buffer size must be {BUFFER_SIZE} bytes, got {len(raw)}"
                )
            return raw, auto_sleep

        options = ConvertOptions(
            dither=request.display_options.dither,
            fit=request.display_options.fit,
            rotate=request.display_options.rotate,
        )
        image = _open_image_bytes(raw)
        try:
            return self._converter.convert_image(image, options=options), auto_sleep
        finally:
            image.close()

    def _validate_request(self, request: DisplayJobRequest) -> None:
        raw = _decode_base64_payload(request.payload_data)
        if request.payload_format == PayloadFormat.NATIVE_BUFFER_BASE64:
            if len(raw) != BUFFER_SIZE:
                raise InvalidRequestError(
                    f"native buffer size must be {BUFFER_SIZE} bytes, got {len(raw)}"
                )
            return

        _open_image_bytes(raw).close()

    def _mark_running(self, job_id: str) -> None:
        with self._jobs_lock:
            record = self._jobs[job_id]
            record.status = JobStatus.RUNNING
            record.started_at = datetime.now(timezone.utc)

    def _mark_succeeded(self, job_id: str) -> None:
        with self._jobs_lock:
            record = self._jobs[job_id]
            record.status = JobStatus.SUCCEEDED
            record.finished_at = datetime.now(timezone.utc)

    def _mark_failed(self, job_id: str, error: str) -> None:
        with self._jobs_lock:
            record = self._jobs[job_id]
            record.status = JobStatus.FAILED
            record.error = error
            record.finished_at = datetime.now(timezone.utc)

    def _queue_position_for(self, job_id: str) -> int | None:
        # queue.Queue has no public iteration API. Accessing `queue` is safe while lock held.
        for idx, queued_id in enumerate(list(self._queue.queue), start=1):  # type: ignore[attr-defined]
            if queued_id == job_id:
                return idx
        return None


class _DeviceSession:
    def __init__(self, factory: DisplayDeviceFactory) -> None:
        self._factory = factory
        self._device: DisplayDevice | None = None

    def __enter__(self) -> DisplayDevice:
        self._device = self._factory()
        return self._device

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._device is not None:
            self._device.close()


def _decode_base64_payload(payload_data: str) -> bytes:
    try:
        return base64.b64decode(payload_data.encode("utf-8"), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise InvalidRequestError("payload_data is not valid base64") from exc


def _open_image_bytes(data: bytes):
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(data))
        image.load()
        return image
    except Exception as exc:
        raise InvalidRequestError("payload_data is not a valid image") from exc
