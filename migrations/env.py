import asyncio
import importlib
import pkgutil
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from alembic import context

import app.modules as modulos
from app.core.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importa el models.py de cada módulo para que sus tablas queden registradas
# en SQLModel.metadata y Alembic las vea al autogenerar. Los módulos sin
# models.py (por ejemplo health) se saltean.
for info in pkgutil.iter_modules(modulos.__path__):
    nombre = f"app.modules.{info.name}.models"
    try:
        importlib.import_module(nombre)
    except ModuleNotFoundError as error:
        if error.name != nombre:
            raise

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse a la base."""
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # La URL viene de DATABASE_URL (.env), nunca de alembic.ini.
    connectable = create_async_engine(
        get_settings().database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
