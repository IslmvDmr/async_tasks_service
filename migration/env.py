from logging.config import fileConfig
import logging

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context

from app.packages.db.base import Base
from app.packages.db.models import Task  # noqa: F401 — нужен для autogenerate
from app.packages.configs import settings

# Alembic Config object
config = context.config

# Настройка логирования через alembic.ini (только если файл указан)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Если хочешь логи без alembic.ini:
# logging.basicConfig(level=logging.INFO)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline mode — только URL, без Engine."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online mode — создаём Engine напрямую из settings."""
    connectable = create_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # опционально: отслеживает изменения типов колонок
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()