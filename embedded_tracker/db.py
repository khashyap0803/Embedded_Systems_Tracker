"""Database utilities for the Embedded Tracker."""

from __future__ import annotations

import os
import platform
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

def _default_data_dir() -> Path:
    home = Path.home()
    system = platform.system().lower()
    if system == "windows":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / "EmbeddedTracker"
    if system == "darwin":
        return home / "Library" / "Application Support" / "EmbeddedTracker"
    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data) if xdg_data else home / ".local" / "share"
    return base / "embedded-tracker"


_DATA_DIR = Path(os.environ.get("EMBEDDED_TRACKER_DATA_DIR", _default_data_dir()))
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _DATA_DIR / "embedded_tracker.db"
_ENGINE = create_engine(f"sqlite:///{_DB_PATH}", echo=False, future=True)


def init_db() -> None:
    """Create database tables if they do not already exist."""
    _apply_migrations()
    SQLModel.metadata.create_all(_ENGINE)


def get_session() -> Session:
    """Return a database session bound to the shared engine."""

    return Session(_ENGINE)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around operations."""

    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _apply_migrations() -> None:
    """Perform lightweight schema migrations for new fields and tables."""

    with _ENGINE.begin() as connection:
        def column_names(table: str) -> set[str]:
            rows = connection.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
            return {row[1] for row in rows}

        # Phase table additions
        if (columns := column_names("phase")):
            if "status" not in columns:
                connection.execute(text("ALTER TABLE phase ADD COLUMN status TEXT DEFAULT 'pending'"))
            if "actual_start" not in columns:
                connection.execute(text("ALTER TABLE phase ADD COLUMN actual_start TEXT"))
            if "actual_end" not in columns:
                connection.execute(text("ALTER TABLE phase ADD COLUMN actual_end TEXT"))
            connection.execute(text("UPDATE phase SET status = 'pending' WHERE status IS NULL"))
            connection.execute(
                text(
                    "UPDATE phase SET status = LOWER(status) WHERE status IN ('PLANNED','IN_PROGRESS','BLOCKED','COMPLETE','COMPLETED')"
                )
            )

        # Week table additions
        if (columns := column_names("week")):
            if "status" not in columns:
                connection.execute(text("ALTER TABLE week ADD COLUMN status TEXT DEFAULT 'pending'"))
            if "actual_start" not in columns:
                connection.execute(text("ALTER TABLE week ADD COLUMN actual_start TEXT"))
            if "actual_end" not in columns:
                connection.execute(text("ALTER TABLE week ADD COLUMN actual_end TEXT"))
            connection.execute(text("UPDATE week SET status = 'pending' WHERE status IS NULL"))
            connection.execute(
                text(
                    "UPDATE week SET status = LOWER(status) WHERE status IN ('PLANNED','IN_PROGRESS','BLOCKED','COMPLETE','COMPLETED')"
                )
            )

        # Day plan table normalisation
        if column_names("dayplan"):
            connection.execute(text("UPDATE dayplan SET status = 'pending' WHERE status IN ('planned','PLANNED')"))
            connection.execute(text("UPDATE dayplan SET status = 'working' WHERE status IN ('in_progress','IN_PROGRESS')"))
            connection.execute(text("UPDATE dayplan SET status = 'paused' WHERE status IN ('blocked','BLOCKED')"))
            connection.execute(
                text(
                    "UPDATE dayplan SET status = 'completed' WHERE status IN ('complete','COMPLETE','completed','COMPLETED')"
                )
            )

        # Task table additions
        if (columns := column_names("task")):
            if "hour_number" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN hour_number INTEGER"))
            if "status" in columns:
                connection.execute(
                    text(
                        "UPDATE task SET status = 'pending' WHERE status IN ('planned', 'in_progress', 'blocked')"
                    )
                )
                connection.execute(text("UPDATE task SET status = 'completed' WHERE status = 'complete'"))
                connection.execute(
                    text(
                        "UPDATE task SET status = LOWER(status) WHERE status IN ('PLANNED','IN_PROGRESS','BLOCKED','COMPLETE','COMPLETED')"
                    )
                )
            if "status_updated_at" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN status_updated_at TEXT"))
            if "first_started_at" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN first_started_at TEXT"))
            if "last_work_started_at" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN last_work_started_at TEXT"))
            if "last_break_started_at" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN last_break_started_at TEXT"))
            if "last_pause_started_at" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN last_pause_started_at TEXT"))
            if "completed_at" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN completed_at TEXT"))
            if "total_work_seconds" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN total_work_seconds INTEGER DEFAULT 0"))
            if "total_break_seconds" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN total_break_seconds INTEGER DEFAULT 0"))
            if "total_pause_seconds" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN total_pause_seconds INTEGER DEFAULT 0"))
            if "day_id" not in columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN day_id INTEGER REFERENCES dayplan(id)"))
            connection.execute(
                text(
                    "UPDATE task SET status_updated_at = COALESCE(status_updated_at, CURRENT_TIMESTAMP)"
                )
            )

