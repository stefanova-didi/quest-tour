"""The stored memories-album PDF (issue #33): rendered once, kept for the host, removable."""

import io
from urllib.parse import parse_qs, urlparse

import pytest
from PIL import Image

from questtour.models import TeamAlbum
from tests.factories import ANSWERS, seed_game
from tests.test_album import play, upload


def jpeg(width=640, height=480, colour=(200, 120, 60)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(out, format="JPEG")
    return out.getvalue()


def png(width=300, height=500) -> bytes:
    out = io.BytesIO()
    Image.new("RGBA", (width, height), (40, 90, 160, 255)).save(out, format="PNG")
    return out.getvalue()


def finish_with_photos(client, token, clock):
    client.post(f"/api/play/{token}/start")
    for position, answer in enumerate(ANSWERS):
        clock.advance(minutes=10)
        play(client, token, "answer", position=position, answer=answer)
        upload(client, token, position, jpeg())
        if position == 1:
            upload(client, token, position, png())
            upload(client, token, position, jpeg(1200, 300))
        play(client, token, "advance", position=position)


@pytest.fixture
def admin(client):
    """The dev provider's magic link signs the admin in on the player client (same cookie jar)."""
    requested = client.post("/api/admin/auth/magic/request", json={"email": "admin@example.com"})
    assert requested.status_code == 200
    params = parse_qs(urlparse(requested.json()["url"]).query)
    verified = client.get(
        "/api/admin/auth/magic/verify",
        params={"token": params["token"][0], "email": params["email"][0]},
        follow_redirects=False,
    )
    assert verified.status_code == 307
    return client


def test_pdf_is_not_ready_during_the_game(client, seed):
    assert client.get(f"/api/play/{seed.token}/album.pdf").status_code == 409


def test_pdf_is_rendered_once_stored_and_served_to_the_team(client, seed, clock, blob_store, session_factory):
    t = seed.token
    finish_with_photos(client, t, clock)
    response = client.get(f"/api/play/{t}/album.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="The-Explorers-memories-album.pdf"'
    data = response.content
    assert data.startswith(b"%PDF-") and 20_000 < len(data) < 2_000_000
    assert data.count(b"/Type /Page\n") + data.count(b"/Type /Page ") >= 5  # cover, 3 chapters, end

    blob = "Sofia-Old-Town-Quest/The-Explorers/2026-10-14_memories-album.pdf"
    assert blob_store.get("albums", blob)[0] == data
    with session_factory() as s:
        record = s.query(TeamAlbum).one()
        assert record.blob_name == blob and record.size_bytes == len(data) and record.deleted_at is None
        generated_at = record.generated_at
    clock.advance(minutes=5)
    assert client.get(f"/api/play/{t}/album.pdf").content == data   # served from storage, not rendered again
    with session_factory() as s:
        assert s.query(TeamAlbum).one().generated_at == generated_at


def test_host_lists_generates_downloads_and_deletes_albums(admin, seed, clock, blob_store, session_factory):
    client = admin
    t = seed.token
    finish_with_photos(client, t, clock)
    rows = client.get("/api/admin/albums").json()
    assert [(r["team_name"], r["end_reason"], r["photo_count"], r["album"]) for r in rows] == [
        ("The Explorers", "finished", 5, None)
    ]
    assignment_id = rows[0]["assignment_id"]

    generated = client.post(f"/api/admin/albums/{assignment_id}/generate").json()
    assert generated["deleted_at"] is None and generated["size_bytes"] > 20_000
    rows = client.get("/api/admin/albums").json()
    assert rows[0]["album"]["id"] == generated["id"]
    download = client.get(f"/api/admin/albums/{generated['id']}/download")
    assert download.status_code == 200 and download.content.startswith(b"%PDF-")
    assert client.get(f"/api/play/{t}/album.pdf").content == download.content   # one file for both

    assert client.delete(f"/api/admin/albums/{generated['id']}").json() == {"deleted": True}
    assert client.get(f"/api/admin/albums/{generated['id']}/download").status_code == 410
    assert client.get(f"/api/play/{t}/album.pdf").status_code == 410            # the team's link too
    assert blob_store.get("albums", "Sofia-Old-Town-Quest/The-Explorers/2026-10-14_memories-album.pdf") is None
    assert client.get("/api/admin/albums").json()[0]["album"]["deleted_at"] is not None

    again = client.post(f"/api/admin/albums/{assignment_id}/generate").json()   # the host changes their mind
    assert again["id"] == generated["id"] and again["deleted_at"] is None
    assert client.get(f"/api/play/{t}/album.pdf").status_code == 200


def test_deleting_a_photo_drops_the_stale_album_so_it_renders_afresh(admin, seed, clock, session_factory):
    client = admin
    t = seed.token
    finish_with_photos(client, t, clock)
    first = client.get(f"/api/play/{t}/album.pdf").content
    photo_id = client.get("/api/admin/photos").json()[0]["id"]
    assert client.delete(f"/api/admin/photos/{photo_id}").json() == {"deleted": True}
    with session_factory() as s:
        assert s.query(TeamAlbum).count() == 0
    second = client.get(f"/api/play/{t}/album.pdf").content
    assert second.startswith(b"%PDF-") and second != first
    with session_factory() as s:
        assert s.query(TeamAlbum).count() == 1


def test_generate_refuses_a_run_that_has_not_ended(admin, seed):
    client = admin
    client.post(f"/api/play/{seed.token}/start")
    assert client.post(f"/api/admin/albums/{seed.assignment_id}/generate").status_code == 409
    assert client.get("/api/admin/albums").json() == []


def test_album_of_a_timed_out_run_renders_its_completed_chapters(client, session_factory, clock):
    with session_factory() as s:
        seed = seed_game(s, clock.now, max_duration_minutes=30)
    t = seed.token
    client.post(f"/api/play/{t}/start")
    play(client, t, "answer", position=0, answer=ANSWERS[0])
    upload(client, t, 0, jpeg())
    play(client, t, "advance", position=0)
    clock.advance(minutes=31)
    response = client.get(f"/api/play/{t}/album.pdf")
    assert response.status_code == 200 and response.content.startswith(b"%PDF-")
