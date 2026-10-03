from datetime import timedelta

import pytest

from questtour.models import Assignment, GameRun, Team
from questtour.services.access import LinkNotValid, ensure_link_usable, find_assignment
from questtour.tokens import hash_token
from tests.factories import seed_game


def add_assignment(session, seed, key, **window):
    base = session.get(Assignment, seed.assignment_id)
    team = Team(host_id="default", key=key, name=key.title(), participants=2)
    assignment = Assignment(
        host_id="default",
        team=team,
        game=base.game,
        token_hash=hash_token(f"{key}-token"),
        exit_message="Bye",
        **window,
    )
    session.add_all([team, assignment])
    session.commit()
    return assignment


def test_find_assignment_returns_match(session_factory, clock):
    with session_factory() as session:
        seed = seed_game(session, clock.now)
        assert find_assignment(session, seed.token).id == seed.assignment_id
        assert find_assignment(session, seed.token, lock=True).id == seed.assignment_id


def test_find_assignment_unknown_token(session_factory, clock):
    with session_factory() as session:
        seed_game(session, clock.now)
        with pytest.raises(LinkNotValid) as exc:
            find_assignment(session, "no-such-token")
        assert exc.value.reason == "unknown"


def test_find_assignment_deactivated_token(session_factory, clock):
    with session_factory() as session:
        seed = seed_game(session, clock.now)
        session.get(Assignment, seed.assignment_id).token_hash = None
        session.commit()
        with pytest.raises(LinkNotValid) as exc:
            find_assignment(session, seed.token)
        assert exc.value.reason == "unknown"


def test_open_window_is_usable(session_factory, clock):
    with session_factory() as session:
        seed = seed_game(session, clock.now)
        assignment = session.get(Assignment, seed.assignment_id)
        ensure_link_usable(assignment, None, clock.now)


def test_not_yet_open_link_rejected(session_factory, clock):
    with session_factory() as session:
        seed = seed_game(session, clock.now)
        opens = clock.now + timedelta(hours=1)
        later = add_assignment(
            session, seed, "later", valid_from=opens, valid_until=opens + timedelta(days=1)
        )
        with pytest.raises(LinkNotValid) as exc:
            ensure_link_usable(later, None, clock.now)
        assert exc.value.reason == "not_yet"
        assert exc.value.opens_at == later.valid_from
        assert exc.value.time_zone == "Europe/Sofia"
        assert exc.value.expired_at is None


def test_expired_link_rejected(session_factory, clock):
    with session_factory() as session:
        seed = seed_game(session, clock.now)
        closes = clock.now - timedelta(minutes=1)
        old = add_assignment(
            session, seed, "old", valid_from=closes - timedelta(days=1), valid_until=closes
        )
        with pytest.raises(LinkNotValid) as exc:
            ensure_link_usable(old, None, clock.now)
        assert exc.value.reason == "expired"
        assert exc.value.expired_at == old.valid_until
        assert exc.value.time_zone == "Europe/Sofia"
        assert exc.value.opens_at is None


def test_window_boundaries(session_factory, clock):
    with session_factory() as session:
        seed = seed_game(session, clock.now)
        edge = add_assignment(
            session,
            seed,
            "edge",
            valid_from=clock.now,
            valid_until=clock.now + timedelta(hours=1),
        )
        ensure_link_usable(edge, None, clock.now)  # now == valid_from is open
        with pytest.raises(LinkNotValid) as exc:
            ensure_link_usable(edge, None, edge.valid_until)  # now == valid_until is closed
        assert exc.value.reason == "expired"


def test_started_run_ignores_window(session_factory, clock):
    with session_factory() as session:
        seed = seed_game(session, clock.now)
        closes = clock.now - timedelta(days=1)
        old = add_assignment(
            session, seed, "old", valid_from=closes - timedelta(days=1), valid_until=closes
        )
        run = GameRun(
            assignment_id=old.id,
            started_at=closes - timedelta(hours=1),
            current_position=0,
            version=1,
        )
        ensure_link_usable(old, run, clock.now)
