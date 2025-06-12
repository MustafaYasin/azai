from collections.abc import Iterable
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from alembic.operations import MigrationScript
from alembic.runtime.migration import MigrationContext
from database import build_engine_url
from database.base import BaseSQLModel
from database.models import *  # noqa: F403

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = BaseSQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
config.set_main_option("sqlalchemy.url", build_engine_url())


def _process_revision_directives(
    context: MigrationContext,  # noqa: ARG001
    revision: str | Iterable[str | None] | Iterable[str],
    directives: list[MigrationScript],
) -> None:
    assert (  # noqa: S101
        len(revision) <= 1
    ), "Only one revision should be passed (not yet capable of handling multiple). See env.py"
    last_revision = 1 if len(revision) == 0 else int(revision[0]) + 1
    rev_id = f"{last_revision:04}"

    for directive in directives:
        directive.rev_id = rev_id


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=_process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=_process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
