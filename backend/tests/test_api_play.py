from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from questtour.models import Assignment, GameRun, Photo, RunDevice, RunTask
from questtour.services.access import LinkNotValid
from questtour.services.game import Outcome
from questtour.storage import StorageUnavailable
from questtour.tokens import hash_token
from tests.factories import ANSWERS, JPEG, OTHER_TOKEN, play_through, seed_game

try:
    from questtour.main import create_app
except ImportError:  # the app factory lands in a later slice: wire just the player router
    create_app = None


@pytest.fixture
def app(settings, session_factory, blob_store, clock):
    if create_app is not None:
        return create_app(
            settings, session_factory=session_factory, blob_store=blob_store, clock=clock
        )
    from questtour.api import play

    app = FastAPI()
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.blob_store = blob_store
    app.state.clock = clock

    @app.exception_handler(LinkNotValid)
    async def link_not_valid(request, exc):
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "link_not_valid",
                    "reason": exc.reason,
                    "opens_at": exc.opens_at.isoformat() if exc.opens_at else None,
                    "expired_at": exc.expired_at.isoformat() if exc.expired_at else None,
                    "time_zone": exc.time_zone,
                }
            },
        )

    app.include_router(play.router)
    return app


def play(client, token, path, **body):
    return client.post(f"/api/play/{token}/{path}", json=body).json()


def upload(client, token, data=JPEG, position=0, **kwargs):
    return client.post(
        f"/api/play/{token}/photo",
        data={"position": str(position)},
        files={"file": ("x.bin", data, "application/octet-stream")},
        **kwargs,
    )


def complete_first(client, token):
    client.post(f"/api/play/{token}/start")
    return play(client, token, "answer", position=0, answer="Alexander Nevsky")


# --- GET state / start -----------------------------------------------------------------------


def test_get_before_start_is_not_started(client, seed):
    r = client.get(f"/api/play/{seed.token}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "not_started" and body["version"] == 0 and body["phase"] is None
    assert body["team"] == {"name": "The Explorers"}


def test_get_does_not_create_a_run(client, seed, session_factory):
    client.get(f"/api/play/{seed.token}")
    with session_factory() as s:
        assert s.query(GameRun).count() == 0


def test_start_creates_run_and_returns_ok(client, seed):
    r = client.post(f"/api/play/{seed.token}/start")
    assert r.status_code == 200
    body = r.json()
    assert body["outcome"] == Outcome.OK
    assert body["state"]["status"] == "playing" and body["state"]["phase"] == "task"
    assert body["state"]["version"] == 1 and body["state"]["position"] == 0
    assert body["state"]["task"]["number"] == 1


def test_start_twice_is_already_started(client, seed, session_factory):
    client.post(f"/api/play/{seed.token}/start")
    r = client.post(f"/api/play/{seed.token}/start").json()
    assert r["outcome"] == "already_started"
    assert r["state"]["status"] == "playing"
    with session_factory() as s:
        assert s.query(GameRun).count() == 1


def test_teams_have_independent_runs(client, seed):
    client.post(f"/api/play/{seed.token}/start")
    assert client.get(f"/api/play/{OTHER_TOKEN}").json()["status"] == "not_started"


# --- token validation -------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["", "/start"])
def test_unknown_token_is_403_link_not_valid(client, seed, path):
    method = client.get if path == "" else client.post
    r = method(f"/api/play/no-such-token{path}")
    assert r.status_code == 403
    assert r.json()["error"] == {
        "code": "link_not_valid",
        "reason": "unknown",
        "opens_at": None,
        "expired_at": None,
        "time_zone": None,
    }


@pytest.mark.parametrize(
    "path,body",
    [
        ("answer", {"position": 0, "answer": "x"}),
        ("hint", {"position": 0, "hint": 1}),
        ("reveal", {"position": 0}),
        ("advance", {"position": 0}),
    ],
)
def test_actions_with_unknown_token_are_403(client, seed, path, body):
    r = client.post(f"/api/play/no-such-token/{path}", json=body)
    assert r.status_code == 403 and r.json()["error"]["reason"] == "unknown"


def test_photo_with_unknown_token_is_403(client, seed):
    assert upload(client, "no-such-token").status_code == 403


def test_not_yet_open_blocks_get_and_start(client, session_factory, clock):
    with session_factory() as s:
        seed = seed_game(s, clock.now, valid_from=clock.now + timedelta(days=1))
    err = client.get(f"/api/play/{seed.token}").json()["error"]
    assert err["reason"] == "not_yet" and err["time_zone"] == "Europe/Sofia" and err["opens_at"]
    r = client.post(f"/api/play/{seed.token}/start")
    assert r.status_code == 403 and r.json()["error"]["reason"] == "not_yet"


def test_expired_without_run_blocks_start(client, session_factory, clock):
    with session_factory() as s:
        seed = seed_game(
            s,
            clock.now,
            valid_from=clock.now - timedelta(days=2),
            valid_until=clock.now - timedelta(hours=1),
        )
    r = client.post(f"/api/play/{seed.token}/start")
    assert r.status_code == 403
    assert r.json()["error"]["reason"] == "expired" and r.json()["error"]["expired_at"]


def test_reissued_token_is_unknown_but_run_survives(client, seed, session_factory):
    client.post(f"/api/play/{seed.token}/start")
    new_token = "new-token-0123456789abcdefghij"
    with session_factory() as s:
        s.get(Assignment, seed.assignment_id).token_hash = hash_token(new_token)
        s.commit()
    assert client.get(f"/api/play/{seed.token}").json()["error"]["reason"] == "unknown"
    assert client.get(f"/api/play/{new_token}").json()["status"] == "playing"


# --- answers ------------------------------------------------------------------------------------


def test_full_run_to_finish(client, seed, clock):
    t = seed.token
    r = client.post(f"/api/play/{t}/start").json()
    assert r["outcome"] == "ok"
    for position, answer in enumerate(ANSWERS):
        clock.advance(minutes=10)
        assert play(client, t, "advance", position=position)["outcome"] == "locked"
        r = play(client, t, "answer", position=position, answer=answer)
        assert r["outcome"] == "correct" and r["state"]["phase"] == "photo"
        assert r["state"]["task"]["landmark"]["name"]
        r = upload(client, t, position=position).json()
        assert r["outcome"] == "ok" and r["state"]["phase"] == "info"
        r = play(client, t, "advance", position=position)
        assert r["outcome"] == "ok"
    state = r["state"]
    assert state["status"] == "finished" and state["phase"] == "results"
    assert state["results"]["total_seconds"] == 30 * 60
    assert state["results"]["leaderboard"] == [
        {
            "rank": 1,
            "team_name": "The Explorers",
            "total_seconds": 1800,
            "hints_used": 0,
            "is_you": True,
        }
    ]


def test_play_through_helper_reaches_finish(client, seed, clock):
    assert play_through(client, seed.token, clock)["status"] == "finished"


def test_wrong_answer_then_correct(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    r = play(client, t, "answer", position=0, answer="Saint Sofia Church")
    assert r["outcome"] == "wrong"
    assert r["state"]["task"]["wrong_attempts"] == 1
    assert r["state"]["clock"]["penalty_minutes"] == 0
    assert r["state"]["phase"] == "task"
    r = play(client, t, "answer", position=0, answer="alexander-nevsky")
    assert r["outcome"] == "correct" and r["state"]["task"]["wrong_attempts"] == 1


def test_second_correct_answer_is_stale(client, seed):
    t = seed.token
    complete_first(client, t)
    r = play(client, t, "answer", position=0, answer="Alexander Nevsky")
    assert r["outcome"] == "stale" and r["state"]["phase"] == "photo"


def test_answer_for_a_future_position_is_stale(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    r = play(client, t, "answer", position=2, answer="Serdika")
    assert r["outcome"] == "stale" and r["state"]["position"] == 0


def test_stale_answer_for_earlier_task_is_logged(client, seed, session_factory):
    t = seed.token
    complete_first(client, t)
    upload(client, t)
    play(client, t, "advance", position=0)
    r = play(client, t, "answer", position=0, answer="Alexander Nevsky")
    assert r["outcome"] == "stale" and r["state"]["position"] == 1
    with session_factory() as s:
        from questtour.models import AnswerAttempt

        assert s.query(AnswerAttempt).count() == 2


def test_action_before_start_is_stale(client, seed):
    t = seed.token
    for path, body in [
        ("answer", {"position": 0, "answer": "x"}),
        ("hint", {"position": 0, "hint": 1}),
        ("reveal", {"position": 0}),
        ("advance", {"position": 0}),
    ]:
        r = client.post(f"/api/play/{t}/{path}", json=body).json()
        assert r["outcome"] == "stale" and r["state"]["status"] == "not_started"
    assert upload(client, t).json()["outcome"] == "stale"


def test_answer_validation_errors_are_422(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    assert (
        client.post(f"/api/play/{t}/answer", json={"position": 0, "answer": ""}).status_code == 422
    )
    assert (
        client.post(f"/api/play/{t}/answer", json={"position": -1, "answer": "x"}).status_code
        == 422
    )
    assert client.post(f"/api/play/{t}/answer", json={"answer": "x"}).status_code == 422
    assert client.post(f"/api/play/{t}/hint", json={"position": 0, "hint": 3}).status_code == 422


def test_secrets_never_sent_during_task(client, seed):
    client.post(f"/api/play/{seed.token}/start")
    body = client.get(f"/api/play/{seed.token}").text
    assert "Alexander Nevsky" not in body
    assert "largest golden domes" not in body


# --- hints / reveal ---------------------------------------------------------------------------


def test_hints_in_order_and_charged_once(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    assert play(client, t, "hint", position=0, hint=2)["outcome"] == "not_available"
    r = play(client, t, "hint", position=0, hint=1)
    assert r["outcome"] == "ok" and r["state"]["clock"]["penalty_minutes"] == 10
    assert play(client, t, "hint", position=0, hint=1)["state"]["clock"]["penalty_minutes"] == 10
    r = play(client, t, "hint", position=0, hint=2)
    assert r["state"]["clock"]["penalty_minutes"] == 25
    assert [h["text"] is not None for h in r["state"]["task"]["hints"]] == [True, True]


def test_hint_that_does_not_exist_is_not_available(client, seed):
    t = seed.token
    complete_first(client, t)
    upload(client, t)
    play(client, t, "advance", position=0)  # task 2 has no hint2
    play(client, t, "hint", position=1, hint=1)
    assert play(client, t, "hint", position=1, hint=2)["outcome"] == "not_available"


def test_reveal_locked_until_unlocked(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    r = play(client, t, "reveal", position=0)
    assert r["outcome"] == "locked" and r["state"]["task"]["completion"] is None


def test_reveal_unlocks_after_n_wrong_attempts(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    for _ in range(5):
        r = play(client, t, "answer", position=0, answer="nope")
    assert r["state"]["task"]["reveal_unlocked"] is True
    r = play(client, t, "reveal", position=0)
    assert r["outcome"] == "ok"
    task = r["state"]["task"]
    assert task["completion"] == "revealed"
    assert task["revealed_answer"] == "Alexander Nevsky Cathedral"
    assert r["state"]["clock"]["penalty_minutes"] == 30
    assert r["state"]["phase"] == "photo"


def test_reveal_unlocks_after_x_minutes(client, seed, clock):
    t = seed.token
    state = play(client, t, "start")["state"]
    assert state["task"]["reveal_unlocks_in_seconds"] == 20 * 60
    clock.advance(minutes=20)
    assert play(client, t, "reveal", position=0)["outcome"] == "ok"


def test_hint_and_reveal_after_completion_are_stale(client, seed):
    t = seed.token
    complete_first(client, t)
    assert play(client, t, "hint", position=0, hint=1)["outcome"] == "stale"
    assert play(client, t, "reveal", position=0)["outcome"] == "stale"


# --- compass --------------------------------------------------------------------------------------


def test_compass_endpoint(client, seed, session_factory):
    t = seed.token
    # Give the current landmark coordinates so the compass is available.
    from questtour.models import Landmark

    with session_factory() as s:
        landmark = s.query(Landmark).filter_by(key="nevsky").one()
        landmark.coordinates_lat = 42.6965
        landmark.coordinates_lon = 23.3331
        s.commit()
    client.post(f"/api/play/{t}/start")
    r = client.post(f"/api/play/{t}/compass").json()
    assert r["outcome"] == "ok"
    assert r["state"]["clock"]["penalty_minutes"] == 5
    assert r["state"]["task"]["compass"]["opened"] is True


def test_compass_after_full_completion_is_stale(client, seed, clock):
    t = seed.token
    play_through(client, t, clock)  # finishes all tasks; current_position == 3
    assert client.post(f"/api/play/{t}/compass").json()["outcome"] == "stale"


def test_compass_not_available_without_coordinates(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    # default fixtures: position-0 landmark has no coordinates
    assert client.post(f"/api/play/{t}/compass").json()["outcome"] == "not_available"


def test_compass_with_coordinates(client, seed, session_factory):
    t = seed.token
    from questtour.models import Landmark

    with session_factory() as s:
        landmark = s.query(Landmark).filter_by(key="nevsky").one()
        landmark.coordinates_lat = 42.6965
        landmark.coordinates_lon = 23.3331
        s.commit()
    client.post(f"/api/play/{t}/start")
    r1 = client.post(f"/api/play/{t}/compass").json()
    assert r1["outcome"] == "ok" and r1["state"]["clock"]["penalty_minutes"] == 5
    r2 = client.post(f"/api/play/{t}/compass").json()
    assert r2["state"]["clock"]["penalty_minutes"] == 5


def test_compass_counts_toward_leaderboard_hints_used(client, seed, session_factory, clock):
    t = seed.token
    from questtour.models import Landmark

    with session_factory() as s:
        landmark = s.query(Landmark).filter_by(key="nevsky").one()
        landmark.coordinates_lat = 42.6965
        landmark.coordinates_lon = 23.3331
        s.commit()
    client.post(f"/api/play/{t}/start")
    assert client.post(f"/api/play/{t}/compass").json()["outcome"] == "ok"
    state = play_through(client, t, clock)
    assert state["status"] == "finished"
    assert state["results"]["leaderboard"] == [
        {
            "rank": 1,
            "team_name": "The Explorers",
            "total_seconds": 1800 + 5 * 60,  # 30 min play + 5 min compass penalty
            "hints_used": 1,
            "is_you": True,
        }
    ]


# --- photos ---------------------------------------------------------------------------------------


def test_photo_before_completion_is_stale(client, seed):
    client.post(f"/api/play/{seed.token}/start")
    assert upload(client, seed.token).json()["outcome"] == "stale"


def test_photo_path_in_game_time_zone_and_suffix(client, seed, blob_store, session_factory):
    t = seed.token
    complete_first(client, t)
    assert upload(client, t).json()["state"]["task"]["photo_count"] == 1
    assert upload(client, t).json()["state"]["task"]["photo_count"] == 2
    base = "Sofia-Old-Town-Quest/The-Explorers/2026-10-14_11-00-00_01_Alexander-Nevsky-Cathedral"
    assert blob_store.get("photos", f"{base}.jpg")[0] == JPEG
    assert blob_store.exists("photos", f"{base}_2.jpg")
    with session_factory() as s:
        assert s.query(Photo).count() == 2


def test_photo_type_is_sniffed_not_trusted(client, seed, blob_store):
    t = seed.token
    complete_first(client, t)
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    r = client.post(
        f"/api/play/{t}/photo",
        data={"position": "0"},
        files={"file": ("x.jpg", png, "image/jpeg")},
    )
    assert r.json()["outcome"] == "ok"
    assert blob_store.exists(
        "photos",
        "Sofia-Old-Town-Quest/The-Explorers/2026-10-14_11-00-00_01_Alexander-Nevsky-Cathedral.png",
    )


def test_photo_rejects_unsupported_type_with_415(client, seed, session_factory):
    t = seed.token
    complete_first(client, t)
    assert upload(client, t, data=b"not an image").status_code == 415
    with session_factory() as s:
        assert s.query(Photo).count() == 0


def test_photo_rejects_too_large_with_413(client, seed, settings, session_factory):
    t = seed.token
    complete_first(client, t)
    settings.max_photo_bytes = 10
    assert upload(client, t).status_code == 413
    with session_factory() as s:
        assert s.query(Photo).count() == 0


@pytest.mark.skipif(create_app is None, reason="needs the app factory's Content-Length guard")
def test_oversized_upload_refused_before_parsing_and_auth(client, seed, settings):
    settings.max_photo_bytes = 0
    big = JPEG + b"\x00" * (1024 * 1024 + 16)
    assert upload(client, "no-such-token", data=big).status_code == 413


def test_photo_position_validation_is_422(client, seed):
    t = seed.token
    complete_first(client, t)
    assert upload(client, t, position=-1).status_code == 422
    r = client.post(f"/api/play/{t}/photo", data={"position": "0"})
    assert r.status_code == 422


def test_photo_for_unreached_task_is_stale(client, seed):
    t = seed.token
    complete_first(client, t)
    assert upload(client, t, position=1).json()["outcome"] == "stale"


def test_late_photo_for_earlier_task_is_stored_against_it(client, seed, session_factory):
    t = seed.token
    complete_first(client, t)
    upload(client, t)
    play(client, t, "advance", position=0)
    r = upload(client, t, position=0).json()
    assert r["outcome"] == "ok" and r["state"]["position"] == 1
    with session_factory() as s:
        first = s.query(RunTask).filter_by(position=0).one()
        assert first.photo_count == 2


def test_photo_storage_outage_is_503(client, seed, blob_store, monkeypatch, session_factory):
    t = seed.token
    complete_first(client, t)

    def boom(*args, **kwargs):
        raise StorageUnavailable("down")

    monkeypatch.setattr(blob_store, "put", boom)
    r = upload(client, t)
    assert r.status_code == 503
    with session_factory() as s:
        assert s.query(Photo).count() == 0


# --- advance -----------------------------------------------------------------------------------------


def test_advance_needs_a_photo(client, seed):
    t = seed.token
    complete_first(client, t)
    assert play(client, t, "advance", position=0)["outcome"] == "locked"
    upload(client, t)
    r = play(client, t, "advance", position=0)
    assert r["outcome"] == "ok" and r["state"]["position"] == 1 and r["state"]["phase"] == "task"


def test_advance_with_stale_position(client, seed):
    t = seed.token
    complete_first(client, t)
    upload(client, t)
    play(client, t, "advance", position=0)
    r = play(client, t, "advance", position=0)
    assert r["outcome"] == "stale" and r["state"]["position"] == 1


# --- time limits ----------------------------------------------------------------------------------------


def test_warning_then_max_duration_game_over(client, seed, clock):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    clock.advance(minutes=225)
    state = client.get(f"/api/play/{t}").json()
    assert state["clock"]["remaining_seconds"] == 900 and state["clock"]["warning"] is True
    clock.advance(minutes=15)
    r = play(client, t, "answer", position=0, answer="Alexander Nevsky")
    assert r["outcome"] == "game_over"
    state = r["state"]
    assert state["status"] == "timed_out" and state["phase"] == "results"
    assert state["results"]["end_reason"] == "max_duration"
    assert state["clock"]["elapsed_seconds"] == 14400
    assert state["results"]["total_seconds"] is None
    assert state["results"]["leaderboard"] == []


@pytest.mark.parametrize(
    "path,body",
    [
        ("hint", {"position": 0, "hint": 1}),
        ("reveal", {"position": 0}),
        ("advance", {"position": 0}),
    ],
)
def test_every_action_after_timeout_is_game_over(client, seed, clock, path, body):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    clock.advance(minutes=241)
    assert client.post(f"/api/play/{t}/{path}", json=body).json()["outcome"] == "game_over"


def test_photo_after_timeout_is_game_over(client, seed, clock):
    t = seed.token
    complete_first(client, t)
    clock.advance(minutes=241)
    assert upload(client, t).json()["outcome"] == "game_over"


def test_playing_run_past_window_becomes_time_is_up(client, session_factory, clock):
    with session_factory() as s:
        seed = seed_game(s, clock.now, valid_until=clock.now + timedelta(hours=1))
    client.post(f"/api/play/{seed.token}/start")
    clock.advance(minutes=61)
    state = client.get(f"/api/play/{seed.token}").json()
    assert state["status"] == "timed_out" and state["phase"] == "results"
    assert state["results"]["end_reason"] == "window_closed"
    assert state["results"]["elapsed_seconds"] == 3600


def test_started_run_stays_reachable_after_window(client, seed, clock):
    client.post(f"/api/play/{seed.token}/start")
    clock.advance(days=30)
    r = client.get(f"/api/play/{seed.token}")
    assert r.status_code == 200 and r.json()["status"] == "timed_out"


def test_finished_run_still_visible_after_window(client, session_factory, clock):
    with session_factory() as s:
        seed = seed_game(s, clock.now, valid_until=clock.now + timedelta(hours=2))
    assert play_through(client, seed.token, clock)["status"] == "finished"
    clock.advance(days=30)
    r = client.get(f"/api/play/{seed.token}")
    assert r.status_code == 200
    assert r.json()["status"] == "finished" and r.json()["phase"] == "results"


# --- version ordering / devices -----------------------------------------------------------------------------


def test_version_increases_on_every_state_change(client, seed):
    t = seed.token
    versions = [play(client, t, "start")["state"]["version"]]
    versions.append(play(client, t, "answer", position=0, answer="nope")["state"]["version"])
    versions.append(play(client, t, "hint", position=0, hint=1)["state"]["version"])
    versions.append(
        play(client, t, "answer", position=0, answer="Alexander Nevsky")["state"]["version"]
    )
    versions.append(upload(client, t).json()["state"]["version"])
    versions.append(play(client, t, "advance", position=0)["state"]["version"])
    assert versions == sorted(set(versions)) and len(versions) == 6


def test_reads_and_noops_do_not_bump_version(client, seed):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    before = client.get(f"/api/play/{t}").json()["version"]
    assert client.get(f"/api/play/{t}").json()["version"] == before
    assert play(client, t, "reveal", position=0)["state"]["version"] == before


def test_devices_are_counted(client, seed, session_factory):
    client.post(f"/api/play/{seed.token}/start")
    client.get(f"/api/play/{seed.token}", headers={"X-Device-Id": "device-bbbb-0002"})
    with session_factory() as s:
        assert s.query(RunDevice).count() == 2


def test_start_registers_the_starting_device(client, seed, session_factory):
    client.post(f"/api/play/{seed.token}/start")
    with session_factory() as s:
        assert [d.device_id for d in s.query(RunDevice)] == ["device-aaaa-0001"]


def test_missing_or_malformed_device_header_is_tolerated(client, seed, session_factory):
    t = seed.token
    client.headers.pop("X-Device-Id")
    assert client.post(f"/api/play/{t}/start").json()["outcome"] == "ok"
    r = client.post(
        f"/api/play/{t}/answer",
        json={"position": 0, "answer": "nope"},
        headers={"X-Device-Id": "bad id!"},
    )
    assert r.json()["outcome"] == "wrong"
    with session_factory() as s:
        assert s.query(RunDevice).count() == 0
        from questtour.models import AnswerAttempt

        assert s.query(AnswerAttempt).one().device_id is None


def test_attempt_records_device_id(client, seed, session_factory):
    t = seed.token
    client.post(f"/api/play/{t}/start")
    play(client, t, "answer", position=0, answer="nope")
    with session_factory() as s:
        from questtour.models import AnswerAttempt

        assert s.query(AnswerAttempt).one().device_id == "device-aaaa-0001"
