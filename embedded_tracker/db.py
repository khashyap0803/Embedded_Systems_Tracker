"""Database utilities for the Embedded Tracker."""

from __future__ import annotations

import os
import platform
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

# Import logging
try:
    from .logging_config import setup_logging
    logger = setup_logging(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


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
try:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    logger.error(f"Failed to create data directory {_DATA_DIR}: {e}")
    raise

_DB_PATH = _DATA_DIR / "embedded_tracker.db"

# v4.0: Thread-safe SQLite configuration for QThreadPool workers
# - check_same_thread=False: Allow connections from multiple threads
# - pool_pre_ping=True: Check connection health before use
_ENGINE = create_engine(
    f"sqlite:///{_DB_PATH}",
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
_SEED_ENV_VAR = "EMBEDDED_TRACKER_SEED_FILE"
_PACKAGE_ROOT = Path(__file__).resolve().parent
_SEED_PATH = _PACKAGE_ROOT / "data" / "roadmap_seed.json"


def init_db() -> None:
    """Create database tables if they do not already exist."""
    try:
        # v4.0: Auto-backup database before migrations to prevent data loss
        if _DB_PATH.exists():
            import shutil
            backup_path = _DB_PATH.with_suffix('.db.bak')
            try:
                shutil.copy2(_DB_PATH, backup_path)
                logger.debug(f"Database backed up to {backup_path}")
            except (OSError, shutil.Error) as backup_error:
                logger.warning(f"Could not create database backup: {backup_error}")
        
        # v4.0: Enable WAL mode for better concurrent access
        with _ENGINE.begin() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
        
        # v4.0: Use Alembic for migrations (preferred method)
        try:
            from alembic.config import Config
            from alembic import command
            
            alembic_cfg = Config(_PACKAGE_ROOT / "alembic.ini")
            alembic_cfg.set_main_option("script_location", str(_PACKAGE_ROOT / "alembic"))
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{_DB_PATH}")
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic migrations applied successfully")
        except ImportError:
            logger.warning("Alembic not available, using legacy migrations")
            _apply_migrations()
        except Exception as alembic_error:
            # Fallback to legacy migrations if Alembic fails
            logger.warning(f"Alembic migration failed, falling back to legacy: {alembic_error}")
            _apply_migrations()
        
        SQLModel.metadata.create_all(_ENGINE)
        logger.info("Database initialized successfully")
    except (sqlite3.Error, OSError) as e:
        logger.error(f"Database initialization failed: {e}")
        raise


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
    except (sqlite3.Error, Exception) as e:
        session.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        session.close()



def _apply_migrations() -> None:
    """Perform lightweight schema migrations for new fields and tables."""
    # Whitelist of valid table names to prevent SQL injection
    VALID_TABLES = {"phase", "week", "dayplan", "task", "project", "certification", 
                    "application", "metric", "resource"}
    
    try:
        with _ENGINE.begin() as connection:
            def column_names(table: str) -> set[str]:
                """Safely get column names for a whitelisted table."""
                if table not in VALID_TABLES:
                    raise ValueError(f"Invalid table name: {table}")
                rows = connection.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
                return {row[1] for row in rows}

            # Phase table additions
            if (columns := column_names("phase")):
                if "status" not in columns:
                    connection.execute(text("ALTER TABLE phase ADD COLUMN status TEXT DEFAULT 'pending'"))
                    logger.info("Added status column to phase table")
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
                    logger.info("Added status column to week table")
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
            
            logger.info("Database migrations applied successfully")
    except (sqlite3.Error, ValueError) as e:
        logger.error(f"Migration failed: {e}")
        raise


def _seed_candidate_paths(explicit: Path | None = None) -> list[Path]:
    """Get list of potential seed file paths in priority order."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    env_path = os.environ.get(_SEED_ENV_VAR)
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(_SEED_PATH)
    # Remove duplicates while preserving order
    unique: list[Path] = []
    for candidate in candidates:
        if candidate and candidate not in unique:
            unique.append(candidate)
    return unique


def ensure_seed_data(seed_path: Path | None = None) -> None:
    """Populate the database with roadmap data if it is currently empty."""

    for candidate in _seed_candidate_paths(seed_path):
        if candidate.exists():
            resolved = candidate
            break
    else:
        return

    # Check if roadmap data already exists
    try:
        with session_scope() as session:
            row = session.execute(text("SELECT 1 FROM phase LIMIT 1")).first()
            if row:
                # Even if roadmap exists, check if hardware needs seeding
                _ensure_hardware_seed()
                return
    except Exception:
        # Table doesn't exist yet - will be created and seeded below
        pass

    # Import lazily to avoid circular dependency during module import.
    from .seed import seed_from_file

    logger.info(f"Auto-seeding roadmap database from {resolved}")
    seed_from_file(resolved)
    
    # Also seed hardware inventory
    _ensure_hardware_seed()


def _ensure_hardware_seed() -> None:
    """Auto-seed hardware inventory from JSON if table is empty."""
    try:
        with session_scope() as session:
            row = session.execute(text("SELECT 1 FROM hardwareitem LIMIT 1")).first()
            if row:
                return  # Hardware already exists
    except Exception:
        # Table might not exist yet on first run
        return
    
    try:
        # Import lazily to avoid circular dependency
        from . import services
        count = services.seed_hardware_from_json()
        if count > 0:
            logger.info(f"Auto-seeded {count} hardware items from inventory JSON")
    except Exception as e:
        logger.warning(f"Could not auto-seed hardware: {e}")



