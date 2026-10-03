import pytest

from questtour.imagetypes import CONFIG_IMAGE_TYPES, HEIC, JPEG, PNG, WEBP, sniff_photo


@pytest.mark.parametrize(
    "head, kind",
    [
        (b"\xff\xd8\xff\xe0\x00\x10JFIF", JPEG),
        (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", PNG),
        (b"RIFF\x24\x00\x00\x00WEBPVP8 ", WEBP),
        (b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00", HEIC),
        (b"\x00\x00\x00\x18ftypmif1\x00\x00\x00\x00", HEIC),
    ],
)
def test_sniff_photo_recognises_accepted_types(head, kind):
    assert sniff_photo(head) == kind


def test_kinds_carry_extension_and_content_type():
    assert (JPEG.ext, JPEG.content_type) == ("jpg", "image/jpeg")
    assert (PNG.ext, PNG.content_type) == ("png", "image/png")
    assert (WEBP.ext, WEBP.content_type) == ("webp", "image/webp")
    assert (HEIC.ext, HEIC.content_type) == ("heic", "image/heic")


@pytest.mark.parametrize("head", [b"GIF89a", b"hello", b"", b"RIFF\x00\x00\x00\x00WAVE"])
def test_sniff_photo_rejects_unknown_formats(head):
    assert sniff_photo(head) is None


def test_config_image_types_include_svg():
    assert CONFIG_IMAGE_TYPES[".svg"] == "image/svg+xml"
    assert CONFIG_IMAGE_TYPES[".jpg"] == "image/jpeg"
