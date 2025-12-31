# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUI Layer (PySide6)                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ MainWindow   │ │ FormDialog   │ │ CustomWidgets│            │
│  │ - Tabs       │ │ - Validation │ │ - StatusPill │            │
│  │ - Menus      │ │ - Fields     │ │ - RippleBtn  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Services Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ services.py                                               │   │
│  │ - list_phases(), create_phase(), update_phase()          │   │
│  │ - list_weeks(), list_days(), list_tasks()                │   │
│  │ - update_task_timing(), transition_status()              │   │
│  │ - Validation helpers                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ db.py        │ │ models.py    │ │ seed.py      │            │
│  │ - Engine     │ │ - Phase      │ │ - Seeding    │            │
│  │ - Sessions   │ │ - Week       │ │ - Upsert     │            │
│  │ - Migrations │ │ - Task       │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SQLite Database                            │
│  ~/.local/share/embedded-tracker/embedded_tracker.db            │
└─────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### `models.py`
- SQLModel ORM definitions
- Database schema with indexes
- Enum definitions (TaskStatus, ProjectStatus, etc.)
- Foreign key relationships

### `db.py`
- SQLAlchemy engine management
- Session handling with context manager
- Schema migrations (ALTER TABLE)
- Database initialization
- Seed data loading

### `services.py`
- Business logic layer
- CRUD operations for all entities
- Data validation
- Record dataclasses for type-safe data transfer
- Timer state management

### `export.py`
- CSV export with proper encoding
- PDF generation with reportlab
- Permission checking
- Error handling

### `utils.py`
- UTC datetime utilities
- Timezone detection
- Duration formatting
- Timer constants

### `logging_config.py`
- Rotating file handler setup
- Console logging for warnings
- Centralized logger configuration

### `gui/main_window.py`
- Main application window
- Tab-based interface for all entities
- Theme management (Ember/Dawn)
- Keyboard shortcuts
- Context menus

### `gui/custom_widgets.py`
- StatusDelegate: Pill-shaped status badges
- RippleButton: Material Design click animation

## Data Flow

1. **User Input** → GUI validates input
2. **GUI** → Calls services.py functions
3. **Services** → Validates business rules, manages transactions
4. **Database** → Persists changes
5. **Services** → Returns typed Record dataclass
6. **GUI** → Updates display

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                       Error Flow                                 │
│                                                                  │
│  User Action                                                     │
│       │                                                          │
│       ▼                                                          │
│  GUI Validation (FormDialog) ──> Show warning if invalid        │
│       │                                                          │
│       ▼                                                          │
│  Services Validation ──> Raise ValueError with message          │
│       │                                                          │
│       ▼                                                          │
│  Database Operation ──> Catch sqlite3.Error, log, re-raise      │
│       │                                                          │
│       ▼                                                          │
│  GUI Exception Handler ──> QMessageBox.critical()               │
│       │                                                          │
│       ▼                                                          │
│  Logger ──> Write to rotating log file                          │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Entity Hierarchy
```
Phase (1)
  └── Week (many)
        ├── DayPlan (many)
        │     └── Task (many)
        ├── Resource (many)
        └── Task (many, without day)

Phase (1)
  ├── Project (many)
  ├── Certification (many)
  └── Metric (many)

Application (standalone)
```

### Key Indexes
- `phase.name` - Quick phase lookup
- `week.number` - Week sorting
- `task.status` - Status filtering
- `task.hour_number` - Hour ordering
