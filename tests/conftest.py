"""Shared pytest fixtures for Embedded Tracker tests."""

from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta

import pytest

# Set test environment before importing application modules
os.environ["EMBEDDED_TRACKER_DATA_DIR"] = tempfile.mkdtemp()


@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary in-memory database for each test."""
    # Create temp directory for test database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Override environment variable
    old_data_dir = os.environ.get("EMBEDDED_TRACKER_DATA_DIR")
    os.environ["EMBEDDED_TRACKER_DATA_DIR"] = temp_dir
    
    yield db_path
    
    # Cleanup
    if old_data_dir:
        os.environ["EMBEDDED_TRACKER_DATA_DIR"] = old_data_dir
    else:
        os.environ.pop("EMBEDDED_TRACKER_DATA_DIR", None)
    
    # Remove temp database file
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_dates():
    """Provide sample dates for testing."""
    today = date.today()
    return {
        "today": today,
        "yesterday": today - timedelta(days=1),
        "tomorrow": today + timedelta(days=1),
        "week_start": today - timedelta(days=today.weekday()),
        "week_end": today + timedelta(days=6 - today.weekday()),
        "month_start": today.replace(day=1),
        "next_month": (today.replace(day=28) + timedelta(days=4)).replace(day=1),
    }


@pytest.fixture
def sample_phase_data(sample_dates):
    """Provide sample phase data for testing."""
    return {
        "name": "Test Phase",
        "description": "A test phase for unit testing",
        "start_date": sample_dates["today"],
        "end_date": sample_dates["next_month"],
    }


@pytest.fixture
def sample_week_data(sample_dates):
    """Provide sample week data for testing."""
    return {
        "number": 1,
        "start_date": sample_dates["week_start"],
        "end_date": sample_dates["week_end"],
        "focus": "Test week focus",
    }


@pytest.fixture
def sample_task_data():
    """Provide sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "A test task for unit testing",
        "estimated_hours": 2.0,
        "ai_prompt": "Test AI prompt",
    }
