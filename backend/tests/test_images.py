import pytest

SVG_NAME = "a" * 64 + ".svg"


@pytest.fixture
def stored_svg(blob_store, settings):
    blob_store.put(settings.images_container, SVG_NAME, b"<svg/>", "image/svg+xml", overwrite=True)


def test_image_is_served_with_immutable_cache_and_safe_headers(client, stored_svg):
    r = client.get(f"/api/images/{SVG_NAME}")

    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert "immutable" in r.headers["cache-control"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.content == b"<svg/>"


@pytest.mark.parametrize(
    "path",
    [
        "/api/images/..%2f..%2fetc%2fpasswd",
        "/api/images/../../etc",
        f"/api/images/{'b' * 64}.svg",  # well-formed but unknown
        "/api/images/not-a-hash.svg",
        f"/api/images/{'A' * 64}.svg",  # upper-case hex is not a stored name
        f"/api/images/{'a' * 64}.exe",
    ],
)
def test_bad_or_unknown_image_names_are_404(client, stored_svg, path):
    assert client.get(path).status_code == 404
