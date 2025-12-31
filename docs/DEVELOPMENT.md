# Development Guide

## Setup Development Environment

### Prerequisites
- Python 3.12+
- Poetry package manager
- Git

### Installation

```bash
# Clone repository
git clone <repo-url>
cd embedded-tracker

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run development version
python -m embedded_tracker.gui.main_window
```

## Code Style

### Formatting
- Follow PEP 8
- Use `ruff` for linting
- Maximum line length: 100 characters
- Use type hints on all functions

### Naming Conventions
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Import Order
1. Standard library
2. Third-party packages
3. Local imports

```python
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlmodel import Session

from .db import session_scope
from .models import Task
```

## Testing

### Run All Tests
```bash
poetry run pytest
```

### Run with Coverage
```bash
poetry run pytest --cov=embedded_tracker
```

### Test Structure
```
tests/
├── conftest.py       # Fixtures
├── test_services.py  # Service layer tests
├── test_models.py    # Model validation
└── test_export.py    # Export functionality
```

## Logging

### Log Location
```
~/.local/share/embedded-tracker/logs/embedded_tracker.log
```

### Log Levels
- DEBUG: Detailed diagnostic information
- INFO: General operational messages
- WARNING: Potential issues
- ERROR: Errors that need attention

### Using the Logger
```python
from .logging_config import setup_logging

logger = setup_logging(__name__)

logger.info("Operation completed")
logger.error(f"Failed: {error}")
```

## Building

### Build .deb Package
```bash
bash scripts/build_linux_deb.sh
```

### Build Output
```
dist/linux/embedded-tracker_0.1.0_amd64.deb
```

### Build Process
1. PyInstaller creates standalone executable
2. Package structure created with proper permissions
3. dpkg-deb generates .deb file

## Database Migrations

### Adding New Column
Edit `db.py` `_apply_migrations()`:

```python
if "new_column" not in columns:
    connection.execute(text("ALTER TABLE task ADD COLUMN new_column TEXT"))
    logger.info("Added new_column to task table")
```

### Adding New Table
1. Define model in `models.py`
2. SQLModel.metadata.create_all() handles creation
3. Add seed data in `seed.py` if needed

## GUI Development

### Adding New Tab
1. Create `class NewEntityTab(BaseCrudTab)` in main_window.py
2. Define `entity_name`, `columns`
3. Implement `fetch_records`, `build_form_fields`, CRUD methods
4. Add to MainWindow.__init__

### Theme Colors
```python
# Ember (Dark)
Background: #121212
Accent: #e67e22 (Orange)
Text: #e0e0e0

# Dawn (Light)
Background: #fffbf0
Accent: #ff7f50 (Coral)
Text: #2d3436
```

### Custom Widget
Create in `gui/custom_widgets.py`:
```python
class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Setup
```

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Run full test suite
- [ ] Run `ruff check` for linting
- [ ] Update CHANGELOG.md
- [ ] Build .deb package
- [ ] Test installation on clean system
- [ ] Tag release in git
