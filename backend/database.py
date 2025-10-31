"""Database utilities for the Creagy project tracker backend."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./creagy_project_tracker.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a transactional SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _create_all() -> None:
    """Create database tables based on the SQLAlchemy metadata."""
    # Import the models module to ensure metadata is populated before creating tables.
    from . import models  # noqa: F401  # pylint: disable=unused-import

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    _create_all()
