from fastapi.testclient import TestClient

from questtour.main import create_app


def test_known_routes_200_unknown_404(tmp_path, settings, session_factory, blob_store, clock):
    (tmp_path / "dist" / "assets").mkdir(parents=True)
    (tmp_path / "dist" / "index.html").write_text("<div id=root></div>", encoding="utf-8")
    (tmp_path / "dist" / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    settings.static_dir = tmp_path / "dist"
    client = TestClient(
        create_app(settings, session_factory=session_factory, blob_store=blob_store, clock=clock)
    )

    assert client.get("/").status_code == 200
    assert client.get("/play/abc").status_code == 200
    assert client.get("/album/abc").status_code == 200
    assert client.get("/album").status_code == 404
    missing = client.get("/play/abc/extra")
    assert missing.status_code == 404 and "id=root" in missing.text
    assert client.get("/assets/app.js").status_code == 200
    api_missing = client.get("/api/nope")
    assert api_missing.status_code == 404
    assert api_missing.headers["content-type"].startswith("application/json")


def test_spa_serves_current_index_html_not_startup_snapshot(
    tmp_path, settings, session_factory, blob_store, clock
):
    """A deploy that replaces index.html must be live without a process restart (web.py reads it on
    every request; the old startup-time snapshot served stale HTML after a green deploy)."""
    (tmp_path / "dist" / "assets").mkdir(parents=True)
    (tmp_path / "dist" / "index.html").write_text("<div id=root>v1</div>", encoding="utf-8")
    settings.static_dir = tmp_path / "dist"
    client = TestClient(
        create_app(settings, session_factory=session_factory, blob_store=blob_store, clock=clock)
    )

    # Replace the deployed file after the app is running, as a new deploy would.
    (tmp_path / "dist" / "index.html").write_text("<div id=root>v2</div>", encoding="utf-8")

    assert "<div id=root>v2</div>" in client.get("/").text
    assert "<div id=root>v2</div>" in client.get("/play/abc").text
    missing = client.get("/play/abc/extra")
    assert missing.status_code == 404 and "<div id=root>v2</div>" in missing.text
