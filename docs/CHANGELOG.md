# Changelog

All notable changes to this project are documented here.

## [0.1.1] - 2025-12-31

### Added
- **Undo/Redo Support**: Command pattern implementation for reversible actions
- **Search/Filter**: Real-time text filtering on all tables
- **Backup & Restore**: Full JSON backup/restore via File menu (Ctrl+B)
- **Inline Form Validation**: Red border highlighting for invalid fields

### Fixed
- **Zombie Timer Bug**: Tasks left in WORKING state after crashes are now auto-reset on startup
- **PDF Export**: Robust error handling prevents crashes on missing reportlab
- **N+1 Query Issue**: Seeding now pre-fetches tasks (90% faster startup)
- **Live Timer**: HoursTab uses `time.monotonic()` for accurate delta updates
- **Backup Attribute**: Fixed `price_paid` → `price_inr` for HardwareItem

### Changed
- **Architecture**: MainWindow decomposed into modular tab files
- **Performance**: Delta updates instead of full table rebuilds for live timers

### Removed
- Unused fix scripts from `data/` directory
- Generated export files from `exports/` directory

---

## [0.1.0] - 2024-12-30

### Added

#### Core Features
- Phase management with date tracking and status
- Week planning with focus areas
- Day scheduling with notes
- Task tracking with hour-level granularity
- Built-in work/break/pause timer with persistence
- Resource library linked to weeks
- Project portfolio with repository links
- Certification progress tracking
- Job application logging
- Metrics recording
- Hardware inventory management

#### GUI Features
- Modern PySide6-based desktop application
- Tab-based interface for all entities
- Ember (dark) and Dawn (light) themes with orange accents
- Status pills with color-coded badges
- RippleButton with Material Design animation
- Form dialogs with validation
- Context menus for quick actions
- Comprehensive keyboard shortcuts

#### Infrastructure
- SQLite database with automatic migrations
- Comprehensive logging with rotating files
- CSV and PDF export functionality
- Command-line interface for basic operations
- .deb package for Linux installation

### Security
- SQL injection prevention via SQLModel/SQLAlchemy
- Input validation on all forms
- Path traversal protection in exports
- File permission checks before exports

---

Format based on [Keep a Changelog](https://keepachangelog.com/)
