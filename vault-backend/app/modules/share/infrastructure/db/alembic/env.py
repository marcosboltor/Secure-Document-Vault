import asyncio
import logging
from logging.config import fileConfig
import sqlalchemy as sa
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings

# Esta es la metadata de SQLModel donde se registrarán todos tus modelos
target_metadata = SQLModel.metadata

# Configuración de logs de Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Ejecutar migraciones en modo 'offline'."""
    url = settings.DB_URL_ASYNC
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: sa.engine.Connection) -> None:
    """Configurar y ejecutar migraciones en una conexión activa."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Ejecutar migraciones en modo 'online'."""
    connectable = create_async_engine(
        settings.DB_URL_ASYNC,
        poolclass=sa.pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
