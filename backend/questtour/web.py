from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

NO_CACHE = {"Cache-Control": "no-cache"}


def install_frontend(app: FastAPI, static_dir: Path | None) -> None:
    """Serve the SPA only for known routes; everything else is a real 404 (technical §3)."""
    if static_dir is not None:
        index_html_path = static_dir / "index.html"
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        # Read index.html on every request, not at startup: a deploy that replaces the file then
        # takes effect without a process restart. A startup snapshot kept serving the old SPA after
        # a green deploy (web.deploy: only /api/health is checked), so workers saw stale HTML.
        def serve_index(status_code: int = 200) -> HTMLResponse:
            return HTMLResponse(
                index_html_path.read_text(encoding="utf-8"),
                status_code=status_code,
                headers=NO_CACHE,
            )

        def spa_home() -> HTMLResponse:
            return serve_index()

        def spa_play(token: str) -> HTMLResponse:
            return serve_index()

        app.add_api_route("/", spa_home, methods=["GET"], include_in_schema=False)
        app.add_api_route("/admin", spa_home, methods=["GET"], include_in_schema=False)
        app.add_api_route("/admin/{path:path}", spa_home, methods=["GET"], include_in_schema=False)
        app.add_api_route("/play/{token}", spa_play, methods=["GET"], include_in_schema=False)

    async def not_found(request: Request, exc: StarletteHTTPException):
        if (
            exc.status_code == 404
            and static_dir is not None
            and not request.url.path.startswith("/api/")
        ):
            return HTMLResponse(
                (static_dir / "index.html").read_text(encoding="utf-8"),
                status_code=404,
                headers=NO_CACHE,
            )  # SPA renders "Page not found"
        return await http_exception_handler(request, exc)

    app.add_exception_handler(StarletteHTTPException, not_found)
