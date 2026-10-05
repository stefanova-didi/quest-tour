import pytest

from questtour.db import quote_ident, set_role
from questtour.settings import Settings


class RecordingConnection:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def exec_driver_sql(self, sql: str) -> None:
        self.calls.append(sql)

    def commit(self) -> None:
        self.calls.append("COMMIT")


@pytest.mark.parametrize(
    "name",
    [
        "questtour_owner",
        "admin@contoso.com",
        "app-quest-tour",
        "admin_x#EXT#@t.onmicrosoft.com",  # Entra guest / Microsoft-account UPN
    ],
)
def test_quote_ident_accepts_entra_names(name):
    assert quote_ident(name) == f'"{name}"'


@pytest.mark.parametrize("bad", ["", 'x"; DROP ROLE y; --', "o'brien", "a" * 64, "tab\tname"])
def test_quote_ident_refuses_names_that_need_escaping(bad):
    with pytest.raises(ValueError):
        quote_ident(bad)


def test_set_role_runs_before_migrations_and_commits():
    conn = RecordingConnection()
    set_role(conn, "questtour_owner")
    assert conn.calls == ['SET ROLE "questtour_owner"', "COMMIT"]


def test_owner_role_setting_defaults_to_none(monkeypatch):
    monkeypatch.delenv("DATABASE_OWNER_ROLE", raising=False)  # _env_file=None only skips .env
    s = Settings(_env_file=None, database_url="sqlite://", public_base_url="http://t")
    assert s.database_owner_role is None


def test_new_team_and_assignment_defaults(session_factory, clock):
    from questtour.models import Assignment, Team
    from tests.factories import seed_game

    with session_factory() as s:
        seed = seed_game(s, clock.now)
        assignment = s.get(Assignment, seed.assignment_id)
        assert assignment.version_floor == 0
        assert assignment.team.is_service is False
        assert all(t.is_service is False for t in s.query(Team))
