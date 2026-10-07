from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

NO_CACHE = {"Cache-Control": "no-cache"}


def install_frontend(app: FastAPI, static_dir: Path | None) -> None:
    """Serve the SPA only for known routes; everything else is a real 404 (technical §3)."""
    index_html: str | None = None
    if static_dir is not None:
        index_html = (static_dir / "index.html").read_text(encoding="utf-8")
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        def spa_home() -> HTMLResponse:
            return HTMLResponse(index_html, headers=NO_CACHE)

        def spa_play(token: str) -> HTMLResponse:
            return HTMLResponse(index_html, headers=NO_CACHE)

        app.add_api_route("/", spa_home, methods=["GET"], include_in_schema=False)
        app.add_api_route("/admin", spa_home, methods=["GET"], include_in_schema=False)
        app.add_api_route("/admin/{path:path}", spa_home, methods=["GET"], include_in_schema=False)
        app.add_api_route("/play/{token}", spa_play, methods=["GET"], include_in_schema=False)

    async def not_found(request: Request, exc: StarletteHTTPException):
        if (
            exc.status_code == 404
            and index_html is not None
            and not request.url.path.startswith("/api/")
        ):
            return HTMLResponse(
                index_html, status_code=404, headers=NO_CACHE
            )  # SPA renders "Page not found"
        return await http_exception_handler(request, exc)

    app.add_exception_handler(StarletteHTTPException, not_found)
