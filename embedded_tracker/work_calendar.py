"""
Work Calendar Module for Embedded Tracker.

This module provides work day calculations that respect weekends and holidays.
It allows scheduling to skip non-working days when calculating week and day dates.

Usage:
    from embedded_tracker.work_calendar import (
        get_calendar_config,
        is_work_day,
        add_work_days,
        next_work_day,
    )
    
    # Check if today is a work day
    if is_work_day(date.today()):
        print("Time to work!")
    
    # Get the date 5 work days from now
    future = add_work_days(date.today(), 5)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional, Set

# Default work days: Monday (0) through Friday (4)
DEFAULT_WORK_DAYS = [0, 1, 2, 3, 4]

# Config file path (stored alongside the database)
_CONFIG_FILE = Path.home() / ".embedded_tracker" / "calendar_config.json"


@dataclass
class CalendarConfig:
    """Configuration for work calendar calculations.
    
    Attributes:
        work_days: List of weekday indices (0=Monday, 6=Sunday) that are work days.
                   Default is Monday-Friday [0,1,2,3,4].
        holidays: List of specific dates that should be treated as non-work days.
        days_per_week: Number of work days to schedule per week (default: 6 for a
                       6-day study week, adjust based on intensity).
    """
    work_days: List[int] = field(default_factory=lambda: DEFAULT_WORK_DAYS.copy())
    holidays: List[date] = field(default_factory=list)
    days_per_week: int = 6  # How many days to schedule tasks per week
    
    def to_dict(self) -> dict:
        """Serialize config to dictionary for JSON storage."""
        return {
            "work_days": self.work_days,
            "holidays": [d.isoformat() for d in self.holidays],
            "days_per_week": self.days_per_week,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> CalendarConfig:
        """Deserialize config from dictionary."""
        return cls(
            work_days=data.get("work_days", DEFAULT_WORK_DAYS.copy()),
            holidays=[date.fromisoformat(d) for d in data.get("holidays", [])],
            days_per_week=data.get("days_per_week", 6),
        )


# Module-level cached config
_cached_config: Optional[CalendarConfig] = None


def get_calendar_config() -> CalendarConfig:
    """Get the current calendar configuration.
    
    Loads from config file if available, otherwise returns defaults.
    Configuration is cached for performance.
    """
    global _cached_config
    
    if _cached_config is not None:
        return _cached_config
    
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text())
            _cached_config = CalendarConfig.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            _cached_config = CalendarConfig()
    else:
        _cached_config = CalendarConfig()
    
    return _cached_config


def save_calendar_config(config: CalendarConfig) -> None:
    """Save calendar configuration to file.
    
    Creates the config directory if it doesn't exist.
    """
    global _cached_config
    
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(config.to_dict(), indent=2))
    _cached_config = config


def clear_config_cache() -> None:
    """Clear the cached configuration, forcing a reload on next access."""
    global _cached_config
    _cached_config = None


def is_work_day(d: date, config: Optional[CalendarConfig] = None) -> bool:
    """Check if a given date is a work day.
    
    A day is a work day if:
    1. Its weekday (0=Mon, 6=Sun) is in the work_days list
    2. It's not in the holidays list
    
    Args:
        d: The date to check.
        config: Optional config override. Uses global config if not provided.
    
    Returns:
        True if the date is a work day, False otherwise.
    """
    if config is None:
        config = get_calendar_config()
    
    # Check if weekday is a work day
    if d.weekday() not in config.work_days:
        return False
    
    # Check if it's not a holiday
    if d in config.holidays:
        return False
    
    return True


def next_work_day(d: date, config: Optional[CalendarConfig] = None) -> date:
    """Get the next work day on or after the given date.
    
    If the given date is a work day, returns it unchanged.
    Otherwise, advances until a work day is found.
    
    Args:
        d: The starting date.
        config: Optional config override.
    
    Returns:
        The next work day (which may be the input date itself).
    """
    if config is None:
        config = get_calendar_config()
    
    while not is_work_day(d, config):
        d = d + timedelta(days=1)
    
    return d


def add_work_days(start: date, days: int, config: Optional[CalendarConfig] = None) -> date:
    """Add a number of work days to a start date.
    
    Skips weekends and holidays when counting days.
    If days is 0, returns the start date (or next work day if start is not a work day).
    
    Args:
        start: The starting date.
        days: Number of work days to add (must be >= 0).
        config: Optional config override.
    
    Returns:
        The date that is 'days' work days after start.
    
    Example:
        # If today is Friday and we add 2 work days:
        # Friday + 2 work days = Tuesday (skipping Sat, Sun)
    """
    if config is None:
        config = get_calendar_config()
    
    if days < 0:
        raise ValueError("days must be non-negative")
    
    # Start from the next work day
    current = next_work_day(start, config)
    
    # Add the specified number of work days
    remaining = days
    while remaining > 0:
        current = current + timedelta(days=1)
        if is_work_day(current, config):
            remaining -= 1
    
    return current


def count_work_days(start: date, end: date, config: Optional[CalendarConfig] = None) -> int:
    """Count the number of work days between two dates (inclusive).
    
    Args:
        start: The start date.
        end: The end date (must be >= start).
        config: Optional config override.
    
    Returns:
        The number of work days in the range [start, end].
    """
    if config is None:
        config = get_calendar_config()
    
    if end < start:
        return 0
    
    count = 0
    current = start
    while current <= end:
        if is_work_day(current, config):
            count += 1
        current = current + timedelta(days=1)
    
    return count


def get_week_date_range(
    start: date,
    days_in_week: int = 6,
    config: Optional[CalendarConfig] = None
) -> tuple[date, date]:
    """Calculate the start and end dates for a week with the given number of work days.
    
    This is used when scheduling weeks to determine how many calendar days
    a "week" of work actually spans.
    
    Args:
        start: The first day of the week.
        days_in_week: Number of work days in this week (default: 6).
        config: Optional config override.
    
    Returns:
        Tuple of (start_date, end_date) where the range contains exactly
        days_in_week work days.
    """
    if config is None:
        config = get_calendar_config()
    
    # Ensure we start on a work day
    start = next_work_day(start, config)
    
    # Find the end date (days_in_week - 1 work days after start)
    if days_in_week <= 1:
        return (start, start)
    
    end = add_work_days(start, days_in_week - 1, config)
    return (start, end)


def list_work_days_in_range(
    start: date,
    end: date,
    config: Optional[CalendarConfig] = None
) -> List[date]:
    """Get all work days in a date range.
    
    Args:
        start: The start date.
        end: The end date.
        config: Optional config override.
    
    Returns:
        List of dates that are work days in the range [start, end].
    """
    if config is None:
        config = get_calendar_config()
    
    work_days = []
    current = start
    while current <= end:
        if is_work_day(current, config):
            work_days.append(current)
        current = current + timedelta(days=1)
    
    return work_days
