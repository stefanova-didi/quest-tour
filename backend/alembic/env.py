from sqlalchemy import create_engine

from alembic import context
from questtour import models  # noqa: F401  (registers tables)
from questtour.db import Base, make_engine, set_role
from questtour.settings import get_settings

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    settings = None if url else get_settings()
    engine = create_engine(url) if url else make_engine(settings)
    with engine.connect() as connection:
        if (
            settings is not None
            and settings.database_owner_role
            and connection.dialect.name == "postgresql"
        ):
            set_role(connection, settings.database_owner_role)
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
