from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from gdey0154f51.pi_server.models import DisplayOptions, JobStatus


class TodoItem(BaseModel):
    text: str = Field(min_length=1)
    done: bool = False


class DisplayImageRequest(BaseModel):
    image_base64: str = Field(min_length=1)
    mime_type: str | None = "image/png"
    source: str | None = None
    client_job_id: str | None = None
    display_options: DisplayOptions = Field(default_factory=DisplayOptions)


class DisplayTextRequest(BaseModel):
    text: str = Field(min_length=1)
    title: str | None = None
    source: str | None = None
    client_job_id: str | None = None
    display_options: DisplayOptions = Field(default_factory=DisplayOptions)


class DisplayTodoRequest(BaseModel):
    title: str = "TODO"
    items: list[TodoItem] = Field(min_length=1)
    source: str | None = None
    client_job_id: str | None = None
    display_options: DisplayOptions = Field(default_factory=DisplayOptions)


class HubJobState(str, Enum):
    ACCEPTED = "ACCEPTED"
    FORWARDED = "FORWARDED"
    FAILED_TO_FORWARD = "FAILED_TO_FORWARD"


class HubJobAccepted(BaseModel):
    job_id: str
    pi_job_id: str


class HubJobStatusResponse(BaseModel):
    job_id: str
    pi_job_id: str | None = None
    hub_status: HubJobState
    pi_status: JobStatus | None = None
    pi_error: str | None = None
    created_at: datetime
    updated_at: datetime
    forward_error: str | None = None
