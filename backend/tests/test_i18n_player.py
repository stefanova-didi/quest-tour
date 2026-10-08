from contextlib import contextmanager

from sqlalchemy import event

from questtour.models import Landmark
from tests.factories import seed_game


@contextmanager
def count_queries(engine, substring):
    counts = {"n": 0}

    def handler(conn, cursor, statement, parameters, context, executemany):
        if substring in statement:
            counts["n"] += 1

    event.listen(engine, "before_cursor_execute", handler)
    try:
        yield counts
    finally:
        event.remove(engine, "before_cursor_execute", handler)


def _make_landmark(session, key, *, name_i18n=None, task_text_i18n=None, hint1_i18n=None):
    lm = Landmark(
        host_id="test",
        key=key,
        name="Base",
        name_i18n=name_i18n,
        task_text="Task base",
        task_text_i18n=task_text_i18n,
        accepted_answers=["1"],
        hint1="Hint base",
        hint1_i18n=hint1_i18n,
        info_text="Info base",
    )
    session.add(lm)
    session.flush()
    return lm


def test_available_languages_is_sorted_union(session_factory, client, clock):
    with session_factory() as session:
        lm1 = _make_landmark(session, "lm1", name_i18n={"de": "D"}, task_text_i18n={"sr": "S"})
        lm2 = _make_landmark(session, "lm2", hint1_i18n={"de": "D2"})
        seed = seed_game(session, clock.now, landmarks=[lm1, lm2])
        token = seed.token
    res = client.get(f"/api/play/{token}")
    assert res.status_code == 200
    assert res.json()["game"]["available_languages"] == ["de", "sr"]


def test_task_returns_i18n_maps(session_factory, client, clock):
    with session_factory() as session:
        lm = _make_landmark(
            session,
            "lm3",
            name_i18n={"de": "Name DE"},
            task_text_i18n={"de": "Task DE"},
            hint1_i18n={"de": "Hint DE"},
        )
        seed = seed_game(session, clock.now, landmarks=[lm])
        token = seed.token
    client.post(f"/api/play/{token}/start", json={})
    client.post(f"/api/play/{token}/hint", json={"position": 0, "hint": 1})
    state = client.get(f"/api/play/{token}").json()
    task = state["task"]
    assert task["text_i18n"] == {"de": "Task DE"}
    assert task["hints"][0]["opened"] is True
    assert task["hints"][0]["text_i18n"] == {"de": "Hint DE"}
    client.post(
        f"/api/play/{token}/answer",
        json={"position": 0, "answer": "1"},
    )
    state = client.get(f"/api/play/{token}").json()
    task = state["task"]
    assert task["landmark"]["name_i18n"] == {"de": "Name DE"}


def test_unopened_hint_does_not_leak_i18n(session_factory, client, clock):
    with session_factory() as session:
        lm = _make_landmark(
            session,
            "lm4",
            hint1_i18n={"de": "Secret DE"},
        )
        seed = seed_game(session, clock.now, landmarks=[lm])
        token = seed.token
    client.post(f"/api/play/{token}/start", json={})
    state = client.get(f"/api/play/{token}").json()
    hint = state["task"]["hints"][0]
    assert hint["opened"] is False
    assert hint["text"] is None
    assert hint["text_i18n"] == {}


def test_not_started_state_avoids_landmark_n_plus_one(session_factory, client, clock, engine):
    with session_factory() as session:
        lms = [_make_landmark(session, f"ns-{i}", name_i18n={"de": f"D{i}"}) for i in range(5)]
        seed = seed_game(session, clock.now, landmarks=lms)
        token = seed.token
    with count_queries(engine, "FROM landmarks") as counts:
        res = client.get(f"/api/play/{token}")
    assert res.status_code == 200
    assert res.json()["game"]["available_languages"] == ["de"]
    assert counts["n"] <= 1


def test_started_state_avoids_landmark_n_plus_one(session_factory, client, clock, engine):
    with session_factory() as session:
        lms = [_make_landmark(session, f"st-{i}", name_i18n={"de": f"D{i}"}) for i in range(5)]
        seed = seed_game(session, clock.now, landmarks=lms)
        token = seed.token
    client.post(f"/api/play/{token}/start", json={})
    with count_queries(engine, "FROM landmarks") as counts:
        res = client.get(f"/api/play/{token}")
    assert res.status_code == 200
    assert counts["n"] <= 2
