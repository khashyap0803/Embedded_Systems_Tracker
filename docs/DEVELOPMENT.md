# Development Guide

> **Version**: 0.2.0  
> **Last Updated**: 2026-01-01  
> **Target Audience**: Contributors, developers, and maintainers

This guide provides comprehensive instructions for setting up, developing, testing, and building the Embedded Systems Tracker application.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Code Style](#code-style)
5. [Database Development](#database-development)
6. [GUI Development](#gui-development)
7. [Testing](#testing)
8. [Building](#building)
9. [Logging](#logging)
10. [Release Checklist](#release-checklist)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Runtime |
| Poetry | 1.8+ | Dependency management |
| Git | 2.40+ | Version control |
| Ubuntu | 22.04+ | Development OS |

### Optional Software

| Software | Purpose |
|----------|---------|
| VS Code | IDE with Python extension |
| SQLite Browser | Database visualization |
| Qt Designer | GUI layout editing |

---

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/khashyap0803/Embedded_Systems_Tracker.git
cd embedded-tracker
```

### 2. Install Dependencies

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 3. Run Development Version

```bash
# Run main application
poetry run python main.py

# Or run directly with Poetry
python -m embedded_tracker.gui.main_window
```

### 4. Seed Database (First Run)

```bash
# Seed with 71-week curriculum
poetry run python scripts/seed_roadmap.py

# Verify seed data
poetry run python scripts/verify_seed.py
```

---

## Project Structure

```
embedded-tracker/
├── main.py                      # Entry point
├── pyproject.toml               # Poetry config (dependencies, metadata)
├── poetry.lock                  # Locked dependencies
│
├── embedded_tracker/            # Main package
│   ├── __init__.py              # Package exports
│   ├── cli.py                   # Command-line interface
│   ├── db.py                    # Database operations
│   ├── export.py                # CSV/PDF export
│   ├── logging_config.py        # Logging setup
│   ├── models.py                # 15 SQLModel ORM classes
│   ├── seed.py                  # Database seeding
│   ├── services.py              # Business logic (CRUD)
│   ├── utils.py                 # Utilities (datetime, formatters)
│   ├── work_calendar.py         # Calendar calculations
│   │
│   ├── data/                    # JSON data files
│   │   ├── roadmap_seed.json    # 71-week curriculum (440KB)
│   │   ├── hardware_bom.json    # Hardware BOM (29KB)
│   │   ├── hardware_inventory.json
│   │   ├── pre_week1_checklist.json
│   │   └── system_specs.json
│   │
│   └── gui/                     # GUI components
│       ├── __init__.py
│       ├── base.py              # BaseCrudTab, FormDialog, delegates
│       ├── main_window.py       # MainWindow class
│       ├── workers.py           # QThread workers
│       └── tabs/                # Tab implementations (10 files)
│           ├── phases.py
│           ├── weeks.py
│           ├── days.py
│           ├── hours.py
│           ├── resources.py
│           ├── projects.py
│           ├── certifications.py
│           ├── applications.py
│           ├── hardware.py
│           └── metrics.py
│
├── scripts/                     # Build & utility scripts
│   ├── build_linux_deb.sh       # Linux .deb builder
│   ├── build_windows_exe.bat    # Windows .exe builder
│   ├── build_windows_exe.ps1    # Windows PowerShell builder
│   ├── seed_roadmap.py          # Database seeding
│   └── verify_seed.py           # Seed verification
│
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   └── test_*.py                # Test modules
│
└── docs/                        # Documentation
    ├── API.md                   # API reference
    ├── ARCHITECTURE.md          # System design
    ├── CHANGELOG.md             # Version history
    └── DEVELOPMENT.md           # This file
```

---

## Code Style

### Formatting Rules

| Rule | Standard |
|------|----------|
| Line length | 100 characters max |
| Indentation | 4 spaces |
| Quotes | Double quotes for strings |
| Docstrings | Google style |
| Type hints | Required on all functions |

### Naming Conventions

```python
# Variables and functions: snake_case
task_count = 0
def list_tasks() -> List[Task]: ...

# Classes: PascalCase
class TaskRecord: ...

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3

# Private methods: _leading_underscore
def _compute_timing(self) -> int: ...
```

### Import Order

```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library
import os
from datetime import datetime, date
from typing import Optional, List

# 3. Third-party packages
from sqlmodel import Session, select
from PySide6.QtWidgets import QWidget

# 4. Local imports
from .db import session_scope
from .models import Task, TaskStatus
```

### Linting

```bash
# Run ruff linter
poetry run ruff check .

# Run ruff with auto-fix
poetry run ruff check --fix .

# Format with black (optional)
poetry run black .
```

---

## Database Development

### Database Location

```
~/.local/share/embedded-tracker/tracker.db
```

### Adding New Column

Edit `db.py` `_apply_migrations()`:

```python
def _apply_migrations(connection):
    # Get existing columns
    result = connection.execute(text("PRAGMA table_info(task)"))
    columns = {row[1] for row in result}
    
    # Add new column if missing
    if "new_column" not in columns:
        connection.execute(text("ALTER TABLE task ADD COLUMN new_column TEXT"))
        logger.info("Migration: Added new_column to task table")
```

### Adding New Table

1. Define model in `models.py`:

```python
class NewEntity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow)
```

2. SQLModel automatically creates table on `init_db()`

3. Add seed data in `seed.py` if needed

### Session Management

```python
from .db import session_scope

def create_task(title: str) -> TaskRecord:
    with session_scope() as session:
        task = Task(title=title)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task_to_record(task)
```

---

## GUI Development

### Adding New Tab

1. Create new file `embedded_tracker/gui/tabs/newtab.py`:

```python
from ..base import BaseCrudTab
from ...models import NewEntity
from ...services import list_new_entities, create_new_entity

class NewEntityTab(BaseCrudTab):
    entity_name = "New Entity"
    
    columns = (
        ("#", "__index__"),
        ("Name", "name"),
        ("Created", "created_at"),
    )
    
    def fetch_records(self):
        return list_new_entities()
    
    def build_form_fields(self, data=None):
        return [
            ("Name", "name", "text", data.get("name", "") if data else ""),
        ]
    
    def do_create(self, data):
        return create_new_entity(**data)
```

2. Register in `main_window.py`:

```python
from .tabs.newtab import NewEntityTab

# In MainWindow.__init__
self.add_tab(NewEntityTab(self.services), "New Entity", "Ctrl+N")
```

### Theme Colors

```python
# Ember (Dark Theme)
EMBER = {
    "background": "#121212",
    "surface": "#1e1e1e",
    "accent": "#e67e22",
    "text_primary": "#e0e0e0",
    "text_secondary": "#b0b0b0",
}

# Dawn (Light Theme)
DAWN = {
    "background": "#fffbf0",
    "surface": "#ffffff",
    "accent": "#ff7f50",
    "text_primary": "#2d3436",
    "text_secondary": "#636e72",
}
```

### Custom Widgets

```python
# In gui/base.py or gui/custom_widgets.py
class StatusPill(QLabel):
    """Color-coded status badge."""
    
    COLORS = {
        "pending": "#95a5a6",
        "working": "#e67e22",
        "completed": "#27ae60",
    }
    
    def __init__(self, status: str, parent=None):
        super().__init__(status.title(), parent)
        self.setStyleSheet(f"""
            background-color: {self.COLORS.get(status, "#95a5a6")};
            border-radius: 10px;
            padding: 4px 12px;
            color: white;
        """)
```

---

## Testing

### Run Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test
poetry run pytest tests/test_services.py::test_create_task
```

### Run with Coverage

```bash
# Generate coverage report
poetry run pytest --cov=embedded_tracker

# Generate HTML report
poetry run pytest --cov=embedded_tracker --cov-report=html
open htmlcov/index.html
```

### Test Structure

```
tests/
├── conftest.py              # Fixtures (test database, sessions)
├── test_models.py           # Model validation tests
├── test_services.py         # Service layer tests
├── test_export.py           # Export functionality tests
└── test_db.py               # Database operations tests
```

### Writing Tests

```python
# tests/test_services.py
import pytest
from embedded_tracker.services import create_task, list_tasks

def test_create_task(test_session):
    """Test task creation with valid data."""
    task = create_task(title="Test Task", week_id=1)
    assert task.title == "Test Task"
    assert task.status == "pending"

def test_list_tasks_empty(test_session):
    """Test listing tasks when none exist."""
    tasks = list_tasks()
    assert tasks == []
```

---

## Building

### Build Linux .deb Package

```bash
# Run build script
bash scripts/build_linux_deb.sh

# Output location
dist/linux/embedded-tracker_0.2.0_amd64.deb

# Install
sudo dpkg -i dist/linux/embedded-tracker_0.2.0_amd64.deb
```

### Build Windows .exe (via PowerShell)

```powershell
# Run build script
.\scripts\build_windows_exe.ps1

# Output location
dist\windows\embedded-tracker.exe
```

### Build Process

1. PyInstaller creates standalone executable from `main.py`
2. Data files bundled from `embedded_tracker/data/`
3. Package structure created with proper permissions
4. `dpkg-deb` generates .deb file (Linux)

---

## Logging

### Log Location

```
~/.local/share/embedded-tracker/logs/embedded_tracker.log
```

### Log Configuration

- **Max file size**: 5MB
- **Backup count**: 3 files
- **Console level**: WARNING
- **File level**: DEBUG

### Using the Logger

```python
from .logging_config import setup_logging

logger = setup_logging(__name__)

logger.debug("Detailed diagnostic info")
logger.info("Operation completed successfully")
logger.warning("Potential issue detected")
logger.error(f"Operation failed: {error}")
logger.exception("Exception occurred", exc_info=True)
```

---

## Release Checklist

### Before Release

- [ ] Update version in `pyproject.toml`
- [ ] Run full test suite: `poetry run pytest`
- [ ] Run linter: `poetry run ruff check`
- [ ] Update `docs/CHANGELOG.md`
- [ ] Update `docs/API.md` if APIs changed
- [ ] Verify data integrity: `poetry run python scripts/verify_seed.py`

### Build & Test

- [ ] Build .deb: `bash scripts/build_linux_deb.sh`
- [ ] Test installation on clean system
- [ ] Verify all tabs load correctly
- [ ] Test timer functionality
- [ ] Test export (CSV/PDF)

### Release

- [ ] Commit all changes
- [ ] Tag release: `git tag -a v0.2.0 -m "Release 0.2.0"`
- [ ] Push: `git push origin main --tags`
- [ ] Create GitHub release with .deb attachment

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `poetry install` to install dependencies |
| Database locked | Close other sqlite connections |
| Timer not updating | Check `time.monotonic()` implementation |
| Theme not applying | Restart application after toggle |

### Reset Database

```bash
# Delete database (WARNING: loses all data)
rm ~/.local/share/embedded-tracker/tracker.db

# Re-seed
poetry run python scripts/seed_roadmap.py
```

### View Logs

```bash
# Tail logs in real-time
tail -f ~/.local/share/embedded-tracker/logs/embedded_tracker.log
```

---

*Development guide follows [Google Engineering Practices](https://google.github.io/eng-practices/) standards.*
