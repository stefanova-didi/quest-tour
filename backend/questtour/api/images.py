import re

from fastapi import APIRouter, HTTPException, Request, Response

from questtour.storage import StorageUnavailable

router = APIRouter()
_NAME = re.compile(r"[0-9a-f]{64}\.(jpg|png|webp|gif|svg)")


@router.get("/api/images/{name}")
def get_image(name: str, request: Request) -> Response:
    if not _NAME.fullmatch(name):
        raise HTTPException(404)
    try:
        found = request.app.state.blob_store.get(request.app.state.settings.images_container, name)
    except StorageUnavailable as exc:
        raise HTTPException(503, "Storage unavailable, please retry") from exc
    if found is None:
        raise HTTPException(404)
    data, content_type = found
    return Response(
        data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",  # inert SVGs
        },
    )
