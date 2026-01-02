"""Centralized utility functions for the Embedded Tracker application."""

from __future__ import annotations

import os
import platform
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore[misc, assignment]


# Public API exports
__all__ = [
    "UTC",
    "utcnow",
    "ensure_utc",
    "normalise_datetimes",
    "seconds_between",
    "get_user_timezone",
    "format_local_datetime",
    "format_duration",
    "sanitize_csv_value",
    # Constants
    "TIMER_REFRESH_MS",
    "POMODORO_WORK_MINUTES",
    "POMODORO_BREAK_MINUTES",
    "LIVE_REFRESH_INTERVAL_MS",
    "IDLE_REFRESH_INTERVAL_MS",
]


# Timer and Pomodoro constants
TIMER_REFRESH_MS = 1000  # Timer refresh interval in milliseconds
POMODORO_WORK_MINUTES = 25  # Standard Pomodoro work session
POMODORO_BREAK_MINUTES = 5  # Standard Pomodoro break

# GUI refresh intervals
LIVE_REFRESH_INTERVAL_MS = 1000   # Refresh interval when task is running (1 second)
IDLE_REFRESH_INTERVAL_MS = 15000  # Refresh interval when idle (15 seconds)


UTC = timezone.utc


def utcnow() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(UTC)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Coerce a datetime to UTC, handling naive datetimes.
    
    If the datetime is naive (no tzinfo), it is assumed to be UTC.
    If the datetime has timezone info, it is converted to UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def normalise_datetimes(values: Iterable[Optional[datetime]]) -> List[datetime]:
    """Filter and normalize a collection of datetimes to UTC.
    
    Skips None values and returns only valid UTC datetimes.
    """
    normalised: List[datetime] = []
    for value in values:
        coerced = ensure_utc(value)
        if coerced is not None:
            normalised.append(coerced)
    return normalised


def seconds_between(start: Optional[datetime], end: datetime) -> int:
    """Calculate the number of seconds between two datetimes.
    
    Both datetimes are normalized to UTC before calculation.
    Returns 0 if start is None or if the result would be negative.
    """
    end_utc = ensure_utc(end)
    start_utc = ensure_utc(start)
    if start_utc is None or end_utc is None:
        return 0
    return max(0, int((end_utc - start_utc).total_seconds()))


def get_user_timezone() -> timezone:
    """Detect the user's system timezone.
    
    Attempts to detect the timezone in this order:
    1. EMBEDDED_TRACKER_TIMEZONE environment variable
    2. System timezone via ZoneInfo
    3. Falls back to UTC if detection fails
    """
    # Check for explicit environment override
    tz_env = os.environ.get("EMBEDDED_TRACKER_TIMEZONE")
    if tz_env:
        try:
            if ZoneInfo is not None:
                return ZoneInfo(tz_env)  # type: ignore[return-value]
        except Exception:
            pass
    
    # Try to detect system timezone
    system = platform.system().lower()
    
    if system == "linux":
        # Try reading /etc/timezone
        try:
            with open("/etc/timezone", "r") as f:
                tz_name = f.read().strip()
                if ZoneInfo is not None and tz_name:
                    return ZoneInfo(tz_name)  # type: ignore[return-value]
        except Exception:
            pass
        
        # Try reading /etc/localtime symlink
        try:
            if os.path.islink("/etc/localtime"):
                link = os.readlink("/etc/localtime")
                # Extract timezone from path like /usr/share/zoneinfo/Asia/Kolkata
                if "zoneinfo/" in link:
                    tz_name = link.split("zoneinfo/")[-1]
                    if ZoneInfo is not None:
                        return ZoneInfo(tz_name)  # type: ignore[return-value]
        except Exception:
            pass
    
    elif system == "darwin":
        # macOS - try reading /etc/localtime symlink
        try:
            if os.path.islink("/etc/localtime"):
                link = os.readlink("/etc/localtime")
                if "zoneinfo/" in link:
                    tz_name = link.split("zoneinfo/")[-1]
                    if ZoneInfo is not None:
                        return ZoneInfo(tz_name)  # type: ignore[return-value]
        except Exception:
            pass
    
    elif system == "windows":
        # Windows - try using tzlocal or registry
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", "(Get-TimeZone).Id"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                tz_name = result.stdout.strip()
                # Windows timezone names need mapping to IANA names
                # For simplicity, use offset-based fallback
                pass
        except Exception:
            pass
    
    # Fallback: calculate offset from system time
    try:
        local_now = datetime.now()
        utc_now = datetime.now(UTC).replace(tzinfo=None)
        offset_seconds = int((local_now - utc_now).total_seconds())
        return timezone(timedelta(seconds=offset_seconds))
    except Exception:
        return UTC


def format_local_datetime(
    value: Optional[datetime],
    fmt: str = "%I:%M %p · %d/%m/%Y",
    tz: Optional[timezone] = None,
) -> str:
    """Format a datetime in the user's local timezone.
    
    Args:
        value: The datetime to format (assumed UTC if naive)
        fmt: strftime format string
        tz: Override timezone (defaults to user's detected timezone)
    
    Returns:
        Formatted datetime string, or empty string if value is None
    """
    if value is None:
        return ""
    
    # Ensure the datetime is timezone-aware
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    
    # Convert to target timezone
    target_tz = tz or get_user_timezone()
    local_value = value.astimezone(target_tz)
    
    return local_value.strftime(fmt)


def format_duration(seconds: float | int | None) -> str:
    """Format a duration in seconds as HH:MM:SS.
    
    Args:
        seconds: Duration in seconds (None treated as 0)
    
    Returns:
        Formatted string like "01:23:45"
    """
    if seconds is None:
        total_seconds = 0
    else:
        total_seconds = max(0, int(round(float(seconds))))
    
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def sanitize_csv_value(value: str | None) -> str:
    """Sanitize a string value for safe CSV export.
    
    Prevents CSV injection attacks by prefixing potentially dangerous
    characters with a single quote, which forces Excel to treat them as text.
    
    Dangerous prefixes: =, @, +, -, tab, carriage return
    
    Args:
        value: String value to sanitize (None returns empty string)
    
    Returns:
        Sanitized string safe for CSV export
        
    Example:
        >>> sanitize_csv_value("=cmd|' /C calc'!A0")
        "'=cmd|' /C calc'!A0"
    """
    if value is None:
        return ""
    
    value_str = str(value)
    
    # Characters that could trigger formula execution in Excel
    dangerous_prefixes = ('=', '@', '+', '-', '\t', '\r')
    
    if value_str and value_str[0] in dangerous_prefixes:
        return f"'{value_str}"
    
    return value_str

