from sqlalchemy import create_engine

from alembic import context
from questtour import models  # noqa: F401  (registers tables)
from questtour.db import Base, make_engine
from questtour.settings import get_settings

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    engine = create_engine(url) if url else make_engine(get_settings())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
