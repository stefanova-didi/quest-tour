import os
import threading

import pytest

from questtour.services import game as rules
from questtour.services.access import find_assignment
from questtour.services.game import Outcome

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="needs PostgreSQL"),
]


def _race(session_factory, token, action):
    """Run `action(session, run)` in two threads that contend for the run lock at the same time."""
    barrier = threading.Barrier(2)
    results = []

    def worker():
        with session_factory() as s:
            assignment = find_assignment(s, token)
            barrier.wait()
            run = rules.load_run(s, assignment.id)  # the second thread blocks here until commit
            results.append(action(s, run))
            s.commit()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    return results


def test_simultaneous_hint_is_charged_once(client, seed, session_factory, clock):
    client.post(f"/api/play/{seed.token}/start")

    _race(session_factory, seed.token, lambda s, run: rules.open_hint(run, 0, 1, clock.now))

    assert client.get(f"/api/play/{seed.token}").json()["clock"]["penalty_minutes"] == 10


def test_simultaneous_correct_answers_give_one_correct_and_one_stale(
    client, seed, session_factory, clock
):
    client.post(f"/api/play/{seed.token}/start")

    results = _race(
        session_factory,
        seed.token,
        lambda s, run: rules.submit_answer(s, run, 0, "Alexander Nevsky", clock.now, "device"),
    )

    assert sorted(results) == sorted([Outcome.CORRECT, Outcome.STALE])


def test_simultaneous_compass_is_charged_once(client, seed, session_factory, clock):
    from questtour.models import Landmark

    with session_factory() as s:
        landmark = s.query(Landmark).filter_by(key="nevsky").one()
        landmark.coordinates_lat = 42.6965
        landmark.coordinates_lon = 23.3331
        s.commit()
    client.post(f"/api/play/{seed.token}/start")
    _race(session_factory, seed.token, lambda s, run: rules.open_compass(run, clock.now))
    assert client.get(f"/api/play/{seed.token}").json()["clock"]["penalty_minutes"] == 5
