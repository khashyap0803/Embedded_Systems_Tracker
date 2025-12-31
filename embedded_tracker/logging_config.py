"""Centralized logging configuration for the Embedded Tracker application."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Import data directory from db module to keep logs in same location
try:
    from .db import _DATA_DIR
    LOG_DIR = _DATA_DIR / "logs"
except ImportError:
    # Fallback for standalone usage
    LOG_DIR = Path.home() / ".local" / "share" / "embedded-tracker" / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(name: str = "embedded_tracker", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger instance with file and console handlers.
    
    Args:
        name: Logger name (typically __name__ of calling module)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        LOG_DIR / "embedded_tracker.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Console handler for WARNING and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Create default logger for the package
logger = setup_logging()
