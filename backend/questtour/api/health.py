import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

log = logging.getLogger("questtour.health")
router = APIRouter()


@router.get("/api/health", include_in_schema=False)
def health(request: Request) -> JSONResponse:
    """App Service health check and deploy smoke test: the app is up and the database answers."""
    try:
        with request.app.state.session_factory() as session:
            session.execute(text("SELECT 1"))
    except Exception:  # driver, network or Entra token errors all mean "not healthy"
        log.exception("health check failed")
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return JSONResponse({"status": "ok"})
