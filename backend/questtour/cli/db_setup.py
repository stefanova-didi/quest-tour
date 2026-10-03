"""One-off production database setup, run by the PostgreSQL Entra admin (infra/README.md, step 5).

Creates the app's managed-identity login role, a NOLOGIN owner role shared by the app identity and the
admins, and the app database owned by that role. Migrations (run by the app) then create tables the
admin's sync-config can write to. Re-running is safe: it only (re)grants memberships."""

import argparse
import sys
from dataclasses import dataclass, field

from sqlalchemy import text

from questtour.db import quote_ident

PG_PORT = 5432


@dataclass(frozen=True)
class DbState:
    current_user: str
    roles: frozenset[str]
    database_exists: bool


@dataclass
class SetupPlan:
    server: list[str] = field(default_factory=list)  # run in the "postgres" database
    database: list[str] = field(default_factory=list)  # run in the app database


def _literal(name: str) -> str:
    quote_ident(name)  # same character whitelist: no quotes, so plain quoting is safe
    return f"'{name}'"


def build_plan(
    state: DbState, *, database: str, app_role: str, owner_role: str, members: list[str]
) -> SetupPlan:
    plan = SetupPlan()
    owner = quote_ident(owner_role)
    if app_role not in state.roles:
        plan.server.append(
            f"SELECT * FROM pgaadauth_create_principal({_literal(app_role)}, false, false)"
        )
    if owner_role not in state.roles:
        plan.server.append(f"CREATE ROLE {owner} NOLOGIN")
    for member in dict.fromkeys([state.current_user, app_role, *members]):
        plan.server.append(f"GRANT {owner} TO {quote_ident(member)} WITH INHERIT TRUE, SET TRUE")
    if state.database_exists:
        plan.database.append(f"GRANT USAGE, CREATE ON SCHEMA public TO {owner}")
    else:
        plan.server.append(f"CREATE DATABASE {quote_ident(database)} OWNER {owner}")
    return plan


def _engine(host: str, user: str, database: str):
    from sqlalchemy import create_engine  # psycopg is imported here, never at module import
    from sqlalchemy.engine import URL

    from questtour.db import use_entra_token_password

    url = URL.create(
        "postgresql+psycopg",
        username=user,
        host=host,
        port=PG_PORT,
        database=database,
        query={"sslmode": "require"},
    )
    engine = create_engine(url, isolation_level="AUTOCOMMIT")  # CREATE DATABASE needs autocommit
    use_entra_token_password(engine)
    return engine


def _read_state(conn, database: str) -> DbState:
    return DbState(
        current_user=conn.execute(text("SELECT current_user")).scalar_one(),
        roles=frozenset(conn.execute(text("SELECT rolname FROM pg_roles")).scalars()),
        database_exists=conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :d"), {"d": database}
        ).first()
        is not None,
    )


def _run(engine, statements: list[str], dry_run: bool) -> None:
    try:
        with engine.connect() as conn:
            for sql in statements:
                print(("-- would run: " if dry_run else "") + sql)
                if not dry_run:
                    conn.exec_driver_sql(sql)
    finally:
        engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="db-setup", description="Create the prod database roles (run once by the PG Entra admin)."
    )
    parser.add_argument("--host", required=True, help="e.g. psql-<app>.postgres.database.azure.com")
    parser.add_argument("--admin-role", required=True, help="your Entra admin UPN or group name")
    parser.add_argument("--app-role", required=True, help="the web app name (its managed identity)")
    parser.add_argument("--database", default="questtour")
    parser.add_argument("--owner-role", default="questtour_owner")
    parser.add_argument("--member", action="append", default=[], help="extra admin role (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="print the statements only")
    args = parser.parse_args(argv)

    try:
        server = _engine(args.host, args.admin_role, "postgres")
        with server.connect() as conn:
            state = _read_state(conn, args.database)
        plan = build_plan(
            state,
            database=args.database,
            app_role=args.app_role,
            owner_role=args.owner_role,
            members=args.member,
        )
        _run(server, plan.server, args.dry_run)
        if plan.database:
            _run(_engine(args.host, args.admin_role, args.database), plan.database, args.dry_run)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("Database roles are ready." if not args.dry_run else "Dry run: nothing was changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
