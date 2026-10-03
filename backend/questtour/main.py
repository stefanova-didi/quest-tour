import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from questtour.api import health, images, play
from questtour.clock import Clock, utc_now
from questtour.db import make_engine
from questtour.services.access import LinkNotValid
from questtour.settings import Settings, get_settings
from questtour.storage import BlobStore, make_blob_store
from questtour.web import install_frontend


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


async def link_not_valid_handler(request: Request, exc: LinkNotValid) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "link_not_valid",
                "reason": exc.reason,
                "opens_at": _iso(exc.opens_at),
                "expired_at": _iso(exc.expired_at),
                "time_zone": exc.time_zone,
            }
        },
    )


log = logging.getLogger("questtour")
UPLOAD_OVERHEAD_BYTES = 1024 * 1024  # multipart boundaries + the position field


def create_app(
    settings: Settings | None = None,
    *,
    session_factory=None,
    blob_store: BlobStore | None = None,
    clock: Clock = utc_now,
) -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    settings = settings or get_settings()
    app = FastAPI(title="Quest City Tour", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.state.session_factory = session_factory or sessionmaker(
        make_engine(settings), expire_on_commit=False
    )
    app.state.blob_store = blob_store or make_blob_store(settings)
    app.state.clock = clock
    if blob_store is None:
        _ensure_containers(app.state.blob_store, settings)

    @app.middleware("http")
    async def refuse_oversized_photo(request: Request, call_next):
        """FastAPI parses (and spools to disk) the whole multipart body before the endpoint runs, before
        the token is even checked. Refuse obviously oversized uploads from Content-Length first."""
        if request.method == "POST" and request.url.path.endswith("/photo"):
            length = request.headers.get("content-length", "")
            if length.isdigit() and int(length) > settings.max_photo_bytes + UPLOAD_OVERHEAD_BYTES:
                return JSONResponse(
                    status_code=413, content={"detail": "Photo is larger than 20 MB"}
                )
        return await call_next(request)

    app.include_router(health.router)
    app.include_router(play.router)
    app.include_router(images.router)
    app.add_exception_handler(LinkNotValid, link_not_valid_handler)
    install_frontend(app, settings.static_dir)
    return app


def _ensure_containers(store: BlobStore, settings: Settings) -> None:
    """A fresh or reset Azurite has no containers. Without this, every upload would be a 503
    until someone re-ran sync-config. Storage being down must not stop the app from starting."""
    try:
        for container in (settings.photos_container, settings.images_container):
            store.ensure_container(container)
    except Exception:  # any SDK/network error: log it; uploads will report 503
        log.exception("could not create blob containers; uploads fail until storage is reachable")
