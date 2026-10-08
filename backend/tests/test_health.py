from fastapi.testclient import TestClient

from questtour.main import create_app
from questtour.version import resolve_version


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "dev"}


def test_health_reports_database_down(settings, blob_store, clock):
    def broken_session_factory():
        raise RuntimeError("database unreachable")

    app = create_app(
        settings, session_factory=broken_session_factory, blob_store=blob_store, clock=clock
    )
    response = TestClient(app).get("/api/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "version": "dev"}


def test_health_is_json_when_the_spa_is_served(
    tmp_path, settings, session_factory, blob_store, clock
):
    # Guards route ordering: the SPA's 404 handler must never shadow the health check.
    (tmp_path / "dist" / "assets").mkdir(parents=True)
    (tmp_path / "dist" / "index.html").write_text("<div id=root></div>", encoding="utf-8")
    settings.static_dir = tmp_path / "dist"
    client = TestClient(
        create_app(settings, session_factory=session_factory, blob_store=blob_store, clock=clock)
    )
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok", "version": "dev"}


def test_health_reports_the_configured_version(settings, session_factory, blob_store, clock):
    settings.app_version = "v1.2.0"
    client = TestClient(
        create_app(settings, session_factory=session_factory, blob_store=blob_store, clock=clock)
    )
    assert client.get("/api/health").json() == {"status": "ok", "version": "v1.2.0"}


def test_version_comes_from_the_packaged_file_unless_overridden(tmp_path, settings):
    version_file = tmp_path / "VERSION"
    assert resolve_version(settings, version_file) == "dev"  # no file, no env: a dev checkout

    version_file.write_text("v1.2.0-3-g6dd4e31\n", encoding="utf-8")
    assert resolve_version(settings, version_file) == "v1.2.0-3-g6dd4e31"

    version_file.write_text("  \n", encoding="utf-8")
    assert resolve_version(settings, version_file) == "dev"  # an empty file is not a version

    settings.app_version = " v9.9.9 "
    assert resolve_version(settings, version_file) == "v9.9.9"  # APP_VERSION wins over the file
