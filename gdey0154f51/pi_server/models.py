from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class PayloadFormat(str, Enum):
    IMAGE_BASE64 = "image_base64"
    NATIVE_BUFFER_BASE64 = "native_buffer_base64"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class DisplayOptions(BaseModel):
    dither: bool = True
    fit: Literal["contain", "cover", "stretch"] = "contain"
    rotate: Literal[0, 90, 180, 270] = 0
    auto_sleep: bool = True


class ContentMeta(BaseModel):
    mime_type: str | None = None
    source: str | None = None
    client_job_id: str | None = None


class DisplayJobRequest(BaseModel):
    payload_format: PayloadFormat
    payload_data: str = Field(min_length=1)
    content_meta: ContentMeta | None = None
    display_options: DisplayOptions = Field(default_factory=DisplayOptions)


class DisplayJobAccepted(BaseModel):
    job_id: str
    queue_position: int


class DisplayJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    error: str | None = None
    queue_position: int | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class HealthResponse(BaseModel):
    ok: bool


class CapabilitiesResponse(BaseModel):
    model: str
    width: int
    height: int
    buffer_size: int
    supported_payload_formats: list[PayloadFormat]
