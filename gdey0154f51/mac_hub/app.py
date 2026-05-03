from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from gdey0154f51.mac_hub.config import MacHubConfig
from gdey0154f51.mac_hub.models import (
    DisplayImageRequest,
    DisplayTextRequest,
    DisplayTodoRequest,
    HubJobAccepted,
    HubJobStatusResponse,
)
from gdey0154f51.mac_hub.pi_client import HttpPiClient
from gdey0154f51.mac_hub.service import MacHubService


def create_app(
    config: MacHubConfig | None = None,
    service: MacHubService | None = None,
) -> FastAPI:
    cfg = config or MacHubConfig.from_env()
    hub_service = service or MacHubService(
        pi_client=HttpPiClient(cfg.pi_base_url, cfg.pi_api_key),
        prefer_native_buffer=cfg.prefer_native_buffer,
    )

    app = FastAPI(title="GDEY0154F51 Mac Hub", version="1.0.0")

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request, exc: RequestValidationError):  # type: ignore[no-untyped-def]
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    @app.post("/api/v1/display/image", response_model=HubJobAccepted, status_code=202)
    async def display_image(body: DisplayImageRequest) -> HubJobAccepted:
        try:
            return await hub_service.submit_image(body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/v1/display/text", response_model=HubJobAccepted, status_code=202)
    async def display_text(body: DisplayTextRequest) -> HubJobAccepted:
        try:
            return await hub_service.submit_text(body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/v1/display/todo", response_model=HubJobAccepted, status_code=202)
    async def display_todo(body: DisplayTodoRequest) -> HubJobAccepted:
        try:
            return await hub_service.submit_todo(body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/api/v1/jobs/{job_id}", response_model=HubJobStatusResponse)
    async def get_job(job_id: str) -> HubJobStatusResponse:
        result = await hub_service.get_job(job_id)
        if result is None:
            raise HTTPException(status_code=404, detail="job not found")
        return result

    return app
