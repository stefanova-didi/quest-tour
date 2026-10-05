from datetime import timedelta

import pytest

from questtour.models import Assignment
from questtour.services import game as rules
from questtour.services.access import find_assignment
from questtour.services.leaderboard import Entry, leaderboard_rows, rank_entries
from tests.factories import add_service_assignment, seed_game


def test_ties_share_rank_and_viewer_is_flagged():
    rows = rank_entries(
        [
            Entry(1, "Sunny Side", 12012, 5),
            Entry(2, "The Explorers", 10710, 3),
            Entry(3, "Night Owls", 9665, 1),
            Entry(4, "Map Breakers", 10710, 2),
        ],
        viewer_run_id=2,
    )
    assert [(r.rank, r.team_name) for r in rows] == [
        (1, "Night Owls"),
        (2, "Map Breakers"),
        (2, "The Explorers"),
        (4, "Sunny Side"),
    ]
    assert [r.is_you for r in rows] == [False, False, True, False]


def test_names_are_sorted_case_insensitively():
    rows = rank_entries(
        [Entry(1, "zebras", 100, 0), Entry(2, "Alpha", 100, 0), Entry(3, "beta", 100, 0)],
        viewer_run_id=None,
    )
    assert [r.team_name for r in rows] == ["Alpha", "beta", "zebras"]
    assert {r.rank for r in rows} == {1}
    assert not any(r.is_you for r in rows)


def test_empty_leaderboard():
    assert rank_entries([], viewer_run_id=1) == []


@pytest.fixture
def session(session_factory):
    with session_factory() as s:
        yield s


def test_leaderboard_rows_only_counts_finished_runs(session, clock):
    seed = seed_game(session, clock.now)
    mine = session.get(Assignment, seed.assignment_id)
    owls = session.query(Assignment).filter(Assignment.id != mine.id).one()

    # The Explorers finish after one hint (10 min penalty); Night Owls are still playing.
    run = rules.start_run(session, mine, clock.now)
    rules.start_run(session, owls, clock.now)
    rules.open_hint(run, 0, 1, clock.now)
    for position, answer in enumerate(["Alexander Nevsky", "Rotunda of St George", "Serdika"]):
        clock.advance(minutes=10)
        rules.submit_answer(session, run, position, answer, clock.now, "d1")
        run.tasks[position].photo_count += 1
        if position < 2:
            rules.advance(run, position, clock.now)
    session.commit()

    rows = leaderboard_rows(session, seed.game_id, viewer_run_id=run.id)
    assert len(rows) == 1
    row = rows[0]
    assert (row.rank, row.team_name, row.hints_used, row.is_you) == (1, "The Explorers", 1, True)
    assert row.total_seconds == int(timedelta(minutes=30 + 10).total_seconds())


def test_leaderboard_rows_skip_service_teams(session, clock):
    seed = seed_game(session, clock.now)
    token = add_service_assignment(session, seed, clock.now)
    assignment = find_assignment(session, token)
    run = rules.start_run(session, assignment, clock.now)
    for position, answer in enumerate(["Alexander Nevsky", "Rotunda of St George", "Serdika"]):
        rules.submit_answer(session, run, position, answer, clock.now, "d1")
        run.tasks[position].photo_count += 1
        if position < 2:
            rules.advance(run, position, clock.now)
    session.commit()
    assert run.end_reason == "finished"
    assert leaderboard_rows(session, seed.game_id, viewer_run_id=run.id) == []
