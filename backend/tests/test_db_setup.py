import pytest

from questtour.cli.db_setup import DbState, build_plan

KW = {"database": "questtour", "app_role": "app-qt", "owner_role": "questtour_owner"}


def test_fresh_server_creates_roles_memberships_and_database():
    state = DbState("admin@contoso.com", frozenset({"azure_pg_admin"}), database_exists=False)
    plan = build_plan(state, members=[], **KW)
    assert plan.server == [
        "SELECT * FROM pgaadauth_create_principal('app-qt', false, false)",
        'CREATE ROLE "questtour_owner" NOLOGIN',
        'GRANT "questtour_owner" TO "admin@contoso.com" WITH INHERIT TRUE, SET TRUE',
        'GRANT "questtour_owner" TO "app-qt" WITH INHERIT TRUE, SET TRUE',
        'CREATE DATABASE "questtour" OWNER "questtour_owner"',
    ]
    assert plan.database == []


def test_rerun_only_refreshes_memberships_and_schema_grant():
    state = DbState(
        "admin@contoso.com",
        frozenset({"app-qt", "questtour_owner", "admin@contoso.com"}),
        database_exists=True,
    )
    plan = build_plan(state, members=["ops@contoso.com", "app-qt"], **KW)
    assert plan.server == [
        'GRANT "questtour_owner" TO "admin@contoso.com" WITH INHERIT TRUE, SET TRUE',
        'GRANT "questtour_owner" TO "app-qt" WITH INHERIT TRUE, SET TRUE',
        'GRANT "questtour_owner" TO "ops@contoso.com" WITH INHERIT TRUE, SET TRUE',
    ]
    assert plan.database == ['GRANT USAGE, CREATE ON SCHEMA public TO "questtour_owner"']


def test_guest_admin_upn_is_supported():
    state = DbState("me_live.com#EXT#@me.onmicrosoft.com", frozenset(), database_exists=False)
    plan = build_plan(state, members=[], **KW)
    assert (
        'GRANT "questtour_owner" TO "me_live.com#EXT#@me.onmicrosoft.com" WITH INHERIT TRUE, SET TRUE'
        in plan.server
    )


def test_refuses_unsafe_names():
    state = DbState("admin@contoso.com", frozenset(), database_exists=False)
    with pytest.raises(ValueError):
        build_plan(state, members=[], database="questtour", app_role="x'); DROP", owner_role="o")
