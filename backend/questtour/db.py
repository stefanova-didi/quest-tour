from datetime import UTC, datetime

from sqlalchemy import DateTime, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

from questtour.settings import Settings


class UTCDateTime(TypeDecorator):
    """Always tz-aware UTC in Python; timestamptz on Postgres, naive-UTC text on SQLite (tests)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetimes are not allowed")
        value = value.astimezone(UTC)
        return value if dialect.name == "postgresql" else value.replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


def make_engine(settings: Settings) -> Engine:
    kwargs: dict = {"pool_pre_ping": True}
    if settings.database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(settings.database_url, **kwargs)
    if settings.database_auth == "azure_ad":
        _use_entra_token_password(engine)
    return engine


def _use_entra_token_password(engine: Engine) -> None:
    """App Service managed identity -> PostgreSQL Flexible Server (technical §2). Not exercised locally."""
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()

    @event.listens_for(engine, "do_connect")
    def _provide_token(dialect, conn_rec, cargs, cparams):
        cparams["password"] = credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        ).token
