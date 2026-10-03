from dataclasses import dataclass


@dataclass(frozen=True)
class ImageKind:
    ext: str
    content_type: str


JPEG = ImageKind("jpg", "image/jpeg")
PNG = ImageKind("png", "image/png")
WEBP = ImageKind("webp", "image/webp")
HEIC = ImageKind("heic", "image/heic")
_HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1", b"heif"}


def sniff_photo(head: bytes) -> ImageKind | None:
    """Accepted photo types (technical §5): JPEG, PNG, HEIC, WebP.

    Detected by magic bytes, not by the client's header.
    """
    if head.startswith(b"\xff\xd8\xff"):
        return JPEG
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return PNG
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return WEBP
    if head[4:8] == b"ftyp" and head[8:12] in _HEIF_BRANDS:
        return HEIC
    return None


# Landmark pictures from config/images (sync-config). SVG allowed (mock art is SVG).
CONFIG_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}
