# Changelog

All notable changes to Embedded Systems Tracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] - 2026-01-02

### 🎉 Major Release - Stanford/MIT Aligned Curriculum

**Complete curriculum overhaul with 10 manual audit passes and ~390 fixes.**

#### Quality Metrics
- **15/15 verification checks passed**
- **0 duplicate tasks** on topic days
- **0 generic patterns** remaining
- **0 content misalignments**
- **1,491 tasks** with **993 unique titles** (66%)

#### Added Topics for 50+ LPA Readiness
- ADC/DAC analog conversion
- Data structures (linked list, hash table)
- JTAG/SWD hardware debugging
- U-Boot bootloader configuration
- FlexRay automotive protocol
- HIL (Hardware-in-the-Loop) testing
- Modbus industrial protocols

#### Curriculum Coverage
| Category | Coverage |
|----------|----------|
| Fundamentals | 100% |
| Hardware | 100% |
| Protocols | 100% |
| RTOS | 100% |
| Automotive | 100% |
| Linux Embedded | 100% |
| Security | 100% |
| Low Power | 100% |
| Testing/Debug | 100% |
| Tools | 100% |
| Career | 100% |

### Changed
- Version bumped from 0.1.0 to 3.0.0
- Updated roadmap_seed.json with all fixes

### Added - Export Features
- **Export All (CSV)**: New menu option (File → Export → Export All CSV)
  - Exports all 9 database tables to individual CSV files
  - Creates combined `all.csv` with all 2,344 records
  - Keyboard shortcut: `Ctrl+Shift+E`
  - Files: phases, weeks, days, tasks, resources, projects, certifications, applications, hardware

---

## [0.1.0] - 2025-12-29

### Initial Release
- 71-week embedded systems curriculum
- 5 phases including Linux Bridge (3.5)
- Desktop application with PySide6
- SQLite database with 15 models
- Timer, themes, backup/restore
