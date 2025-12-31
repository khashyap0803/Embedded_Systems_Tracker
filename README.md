# 🔧 Embedded Systems Tracker

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-6.0+-green.svg" alt="PySide6">
  <img src="https://img.shields.io/badge/SQLite-3.0+-orange.svg" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

A comprehensive desktop application for tracking progress through a 59-week embedded systems learning roadmap. Built with Python, PySide6, and SQLite.

---

## ✨ Features

### 📊 Roadmap Management
| Feature | Description |
|---------|-------------|
| **Phase Tracking** | High-level 4-phase learning periods with dates and progress |
| **Week Planning** | 59 weeks with focus areas and milestones |
| **Day Scheduling** | Day-by-day task planning with notes |
| **Task Tracking** | Hour-level work items with time tracking |

### ⏱️ Time Management
| Feature | Description |
|---------|-------------|
| **Live Timer** | Built-in work/break/pause timer with persistence |
| **Zombie Timer Fix** | Auto-reset stale tasks on startup |
| **Time Reports** | Track work, break, and pause hours |

### 📚 Resource Management
| Feature | Description |
|---------|-------------|
| **Resource Library** | Study materials linked to weeks |
| **Project Portfolio** | Track projects with repo/demo links |
| **Certifications** | Monitor certification progress |
| **Job Applications** | Log applications and status |
| **Hardware Inventory** | Track development boards and components |

### 🎨 User Experience
| Feature | Description |
|---------|-------------|
| **Dark/Light Themes** | Ember and Dawn themes with orange accents |
| **Search & Filter** | Real-time text filtering on all tables |
| **Undo/Redo** | Reversible delete operations |
| **Backup/Restore** | Full JSON backup and restore |
| **Keyboard Shortcuts** | Comprehensive shortcut support |
| **Form Validation** | Inline validation with red borders |

### 📤 Export & Reports
| Feature | Description |
|---------|-------------|
| **CSV Export** | Export tasks and roadmap to CSV |
| **PDF Reports** | Generate PDF reports with formatting |

---

## 🚀 Installation

### From .deb Package (Recommended for Linux)
```bash
# Install the package
sudo dpkg -i dist/linux/embedded-tracker_0.1.0_amd64.deb

# Launch the application
embedded-tracker
```

### From Source (Development)
```bash
# Clone repository
git clone https://github.com/yourusername/embedded-tracker.git
cd embedded-tracker

# Install with Poetry
poetry install

# Run application
poetry run python main.py
```

---

## 📁 Project Structure

```
embedded-tracker/
├── README.md                    # This file
├── pyproject.toml               # Poetry configuration
├── main.py                      # Entry point
│
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # System design
│   ├── CHANGELOG.md             # Version history
│   ├── DEVELOPMENT.md           # Developer guide
│   └── API.md                   # API reference
│
├── embedded_tracker/            # Main Python package
│   ├── __init__.py              # Package exports
│   ├── cli.py                   # CLI interface
│   ├── db.py                    # Database operations
│   ├── export.py                # CSV/PDF export
│   ├── models.py                # SQLModel ORM
│   ├── seed.py                  # Data seeding
│   ├── services.py              # Business logic
│   ├── utils.py                 # Utilities
│   ├── work_calendar.py         # Calendar utilities
│   │
│   ├── data/                    # Data files
│   │   ├── roadmap_seed.json    # 59-week roadmap
│   │   ├── hardware_*.json      # Hardware inventory
│   │   └── *.json               # Configuration files
│   │
│   └── gui/                     # GUI components
│       ├── base.py              # Base classes
│       ├── main_window.py       # Main window
│       ├── workers.py           # Background threads
│       └── tabs/                # Tab implementations
│
├── scripts/                     # Build scripts
│   └── build_linux_deb.sh       # Linux .deb builder
│
└── tests/                       # Test suite
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | Add new record |
| `Ctrl+E` | Edit selected record |
| `Delete` | Delete selected record |
| `Ctrl+R` | Refresh current tab |
| `Ctrl+Shift+A` | Refresh all tabs |
| `Ctrl+Z` | Undo last action |
| `Ctrl+Y` | Redo last action |
| `Ctrl+B` | Create backup |
| `Ctrl+D` | Toggle dark/light theme |
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |
| `Ctrl+1-9` | Go to specific tab |
| `Escape` | Clear selection |
| `Ctrl+Q` | Quit application |

---

## 💾 Data Storage

| Data | Location |
|------|----------|
| Database | `~/.local/share/embedded-tracker/embedded_tracker.db` |
| Logs | `~/.local/share/embedded-tracker/logs/` |
| Backups | User-specified location (JSON format) |

---

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Poetry package manager
- PySide6

### Setup
```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Build .deb package
bash scripts/build_linux_deb.sh
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development guide.

---

## 📋 CLI Commands

```bash
# List tasks
embedded-tracker list --week 1

# Show today's tasks
embedded-tracker today

# List resources
embedded-tracker resources

# List projects
embedded-tracker projects
```

---

## 🔒 Security

- **SQL Injection Protection**: All queries via SQLModel/SQLAlchemy
- **Path Traversal Prevention**: Export path validation
- **Input Validation**: All form inputs validated
- **Zombie Timer Protection**: Stale tasks auto-reset on startup

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [PySide6](https://wiki.qt.io/Qt_for_Python) - Qt bindings for Python
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases with Python
- [ReportLab](https://www.reportlab.com/) - PDF generation
- [Rich](https://github.com/Textualize/rich) - CLI formatting

---

<p align="center">
  Made with ❤️ for embedded systems enthusiasts
</p>
