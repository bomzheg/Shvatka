import asyncio
import logging.config

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from shvatka.infrastructure.db.models import Base

config = context.config

logging.config.fileConfig(config.config_file_name)  # type: ignore

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = AsyncEngine(
        create_engine(
            url=config.get_main_option("sqlalchemy.url"),
            poolclass=pool.NullPool,
        )
    )

    async with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
