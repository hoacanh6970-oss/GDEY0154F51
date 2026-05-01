from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from gdey0154f51.constants import BUFFER_SIZE, HEIGHT, WIDTH
from gdey0154f51.driver import GDEY0154F51
from gdey0154f51.pi_server.config import PiServerConfig
from gdey0154f51.pi_server.models import (
    CapabilitiesResponse,
    DisplayJobAccepted,
    DisplayJobRequest,
    DisplayJobStatusResponse,
    HealthResponse,
    PayloadFormat,
)
from gdey0154f51.pi_server.service import (
    InvalidRequestError,
    PiDisplayService,
    QueueFullError,
)


def _build_default_service(config: PiServerConfig) -> PiDisplayService:
    def _factory() -> GDEY0154F51:
        return GDEY0154F51.from_rpi(
            pin_config=config.pin_config,
            spi_config=config.spi_config,
            busy_timeout_s=config.busy_timeout_s,
        )

    return PiDisplayService(device_factory=_factory, queue_max_size=config.queue_max_size)


def create_app(
    config: PiServerConfig | None = None,
    service: PiDisplayService | None = None,
) -> FastAPI:
    cfg = config or PiServerConfig.from_env()
    display_service = service or _build_default_service(cfg)

    app = FastAPI(title="GDEY0154F51 Pi Server", version="1.0.0")

    @app.on_event("startup")
    def _startup() -> None:
        display_service.start()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        display_service.stop()

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request, exc: RequestValidationError):  # type: ignore[no-untyped-def]
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
        if x_api_key != cfg.api_key:
            raise HTTPException(status_code=401, detail="invalid api key")

    @app.get("/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(ok=True)

    @app.get("/v1/capabilities", response_model=CapabilitiesResponse)
    def capabilities() -> CapabilitiesResponse:
        return CapabilitiesResponse(
            model="GDEY0154F51",
            width=WIDTH,
            height=HEIGHT,
            buffer_size=BUFFER_SIZE,
            supported_payload_formats=[
                PayloadFormat.IMAGE_BASE64,
                PayloadFormat.NATIVE_BUFFER_BASE64,
            ],
        )

    @app.post(
        "/v1/jobs/display",
        response_model=DisplayJobAccepted,
        status_code=202,
        dependencies=[Depends(require_api_key)],
    )
    def submit_display_job(body: DisplayJobRequest) -> DisplayJobAccepted:
        try:
            job_id, queue_position = display_service.submit_job(body)
        except InvalidRequestError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except QueueFullError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        return DisplayJobAccepted(job_id=job_id, queue_position=queue_position)

    @app.get(
        "/v1/jobs/{job_id}",
        response_model=DisplayJobStatusResponse,
        dependencies=[Depends(require_api_key)],
    )
    def get_job(job_id: str) -> DisplayJobStatusResponse:
        result = display_service.get_job(job_id)
        if result is None:
            raise HTTPException(status_code=404, detail="job not found")
        return result

    return app
