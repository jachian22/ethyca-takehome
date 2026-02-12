from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "tic_tac_toe.db"

_engine = None


def _resolve_database_url(database_url: str | None = None) -> str:
    if database_url:
        return _normalize_database_url(database_url)

    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return _normalize_database_url(env_url)

    env_url = os.getenv("TICTACTOE_DATABASE_URL")
    if env_url:
        return _normalize_database_url(env_url)

    return f"sqlite:///{DEFAULT_DB_PATH}"


def _normalize_database_url(raw_url: str) -> str:
    # Railway and other providers often expose postgres:// by default.
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


def init_engine(database_url: str | None = None):
    global _engine
    resolved_url = _resolve_database_url(database_url)
    connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
    _engine = create_engine(resolved_url, connect_args=connect_args, pool_pre_ping=True)
    return _engine


def get_engine():
    global _engine
    if _engine is None:
        _engine = init_engine()
    return _engine


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
