import logging
import secrets
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

log = logging.getLogger(__name__)


class FieldError(BaseModel):
    field: str
    message: str


class ConflictError(Exception):
    def __init__(self, entity: str, current: dict):
        self.entity = entity
        self.current = current


class AdminValidationError(Exception):
    def __init__(self, errors: list[FieldError]):
        self.errors = errors


def _pydantic_errors(exc: PydanticValidationError) -> list[FieldError]:
    return [
        FieldError(field=".".join(str(p) for p in e["loc"]), message=e["msg"]) for e in exc.errors()
    ]


def _request_validation_errors(exc: RequestValidationError) -> list[FieldError]:
    return [
        FieldError(field=".".join(str(p) for p in e["loc"]), message=e["msg"]) for e in exc.errors()
    ]


def _is_admin_path(path: str) -> bool:
    return path.startswith("/api/admin/")


def _request_reference() -> str:
    """Short, url-safe reference for the admin UI to show while full details stay server-side."""
    return secrets.token_urlsafe(8)


def _json_safe(value):
    if isinstance(value, datetime):
        return value.astimezone(UTC).replace(microsecond=0).isoformat()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def register_admin_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AdminValidationError)
    async def _422(request: Request, exc: AdminValidationError):
        return JSONResponse(
            status_code=422,
            content={"errors": [e.model_dump() for e in exc.errors]},
        )

    @app.exception_handler(RequestValidationError)
    async def _request_validation_422(request: Request, exc: RequestValidationError):
        # Player routes keep FastAPI's default {detail: [...]} shape unchanged.
        if not _is_admin_path(request.url.path):
            return await request_validation_exception_handler(request, exc)
        return JSONResponse(
            status_code=422,
            content={"errors": [e.model_dump() for e in _request_validation_errors(exc)]},
        )

    @app.exception_handler(ConflictError)
    async def _409(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=409,
            content={"entity": exc.entity, "current": _json_safe(exc.current)},
        )

    @app.exception_handler(Exception)
    async def _500(request: Request, exc: Exception):
        if not _is_admin_path(request.url.path):
            raise exc
        ref = _request_reference()
        log.exception("unhandled admin error (reference=%s)", ref)
        return JSONResponse(
            status_code=500,
            content={"reference": ref},
        )
