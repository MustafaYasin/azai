import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from database.settings import settings

_engine = None
_sessionmaker = None
_initialized = False


def build_engine_url() -> str:
    return f"postgresql://{settings.postgres_username}:{settings.postgres_password}@{settings.postgres_host}:5432/{settings.postgres_database}"


def setup_database() -> None:
    global _engine, _sessionmaker, _initialized  # noqa: PLW0603

    _engine = create_engine(build_engine_url())
    _sessionmaker = sessionmaker(_engine, class_=Session)

    _initialized = True


def open_session() -> Session:
    if sys.argv[0].endswith("alembic"):
        msg = "open_session() should not be called FROM an alembic subprocess"
        raise RuntimeError(msg)

    if not _initialized:
        setup_database()

    # noinspection PyCallingNonCallable
    return _sessionmaker()
