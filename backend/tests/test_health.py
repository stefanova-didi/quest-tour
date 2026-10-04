from fastapi.testclient import TestClient

from questtour.main import create_app


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_reports_database_down(settings, blob_store, clock):
    def broken_session_factory():
        raise RuntimeError("database unreachable")

    app = create_app(
        settings, session_factory=broken_session_factory, blob_store=blob_store, clock=clock
    )
    response = TestClient(app).get("/api/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


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
    assert response.json() == {"status": "ok"}
