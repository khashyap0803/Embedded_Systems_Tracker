# Embedded Systems Tracker — Context

## Product vision
- Single desktop companion to execute a 52-week embedded systems mastery plan covering hardware foundations through productization.
- Tracks every phase → week → day → hour, plus supporting resources, projects, certifications, applications, and metrics.
- Ships as a standalone GUI (PySide6) with a parity CLI so you can review or update progress from scripts or terminals.

## Architecture snapshot
- **Language/runtime:** Python 3.12 managed by Poetry.
- **Storage:** SQLite via SQLModel; tables for phases, weeks, days, tasks, resources, projects, certifications, applications, metrics.
- **Domain helpers:** `embedded_tracker.services` exposes CRUD + status transitions; `embedded_tracker.db` wraps engine/init, lightweight migrations, and auto-seeding.
- **Interface layers:**
  - `embedded_tracker/gui/main_window.py` hosts tabbed CRUD views (Phases, Weeks, Days, Hours, Resources, Projects, Certifications, Applications, Metrics) with timezone-aware formatting and live task timers.
  - `embedded_tracker/cli.py` mirrors the same data for quick terminal summaries.
- **Packaging:** `main.py` launches the GUI; `scripts/build_linux_deb.sh` drives PyInstaller + Debian packaging, bundling a seed JSON so fresh installs auto-populate data.

## Data + seeding flow
1. `scripts/generate_full_seed.py` builds `data/roadmap_seed.json` **and** `embedded_tracker/data/roadmap_seed.json` (packaged copy) with the curated 52-week curriculum.
2. `embedded_tracker/seed.py` owns all insert/upsert logic; `scripts/seed_roadmap.py` is the thin CLI wrapper.
3. On start, `embedded_tracker.db.ensure_seed_data()` looks for a JSON path in order: explicit argument → `EMBEDDED_TRACKER_SEED_FILE` env → repo `data/` → packaged `embedded_tracker/data/`. If the SQLite DB is empty, it seeds automatically.

## Notable implementation details
- **Timezone safety:** All timestamps are coerced to timezone-aware UTC via `_ensure_utc`; container roll-ups (day/week/phase actual start/end) now normalise datetimes before comparisons to avoid "can't compare offset-naive and offset-aware" errors, and `_normalise_datetimes` keeps historical snapshots stable even when raw records were saved as naive timestamps.
- **Hours tab polish:**
  - Work/Break/Pause durations display as `HH:MM:SS` timers derived from tracked seconds, so increments happen only after real elapsed seconds.
  - Live tasks refresh every second while running/break/pause, but fall back to 15s polling when idle to limit repaint cost.
  - Context menu status changes propagate through day/week/phase hierarchies instantly.
- **Rest-day overrides:** Day 7 is auto-generated without hour tasks, timer math skips it, and the Days tab exposes a context-menu override so you can manually mark rest days complete (or paused, etc.) and still allow the parent week to close cleanly. Under the hood `services.override_day_status()` recalculates aggregates immediately so downstream roll-ups remain accurate.
- **CLI output:** `embedded-tracker list|today|projects|...` renders rich tables with logged hours computed from active timers, and now calls `ensure_seed_data()` on startup so scripted usage never hits an empty DB.
- **GUI bootstrap:** `main.py` invokes `ensure_seed_data()` before showing the PySide6 window, guaranteeing the same populated experience as the CLI.
- **Packaging niceties:** Auto-seeding guarantees a populated dataset even in PyInstaller builds; Debian install script copies the binary + desktop entry into `/usr/local`.

## Recent enhancements
- Rebuilt the roadmap generator to cover the full 52-week curriculum with projects, certifications, applications, and metrics metadata.
- Re-sequenced Phase 1 so the first 8 weeks now drill electronics fundamentals, digital logic, C syntax mastery, and UART/I2C/SPI basics before moving into advanced hardware bring-up.
- Extended Phase 2 with RISC-V + ESP32-C3 bring-up labs, dual-stack connectivity, and Android companion provisioning flows while keeping the Zephyr/FreeRTOS rigor intact.
- Added Android Automotive HAL integration, AAOS security workflows, and AI observability weeks (model drift, incident playbooks) so later phases cover in-car experiences and MLOps hardening.
- Centralised seeding logic (`embedded_tracker.seed`) so the CLI, GUI, and installer all share the same insert paths.
- Added live auto-seeding on first run plus packaged JSON assets, ensuring the GUI never launches empty, and wired both the CLI and GUI entrypoints to call `ensure_seed_data()` up front.
- Fixed Hours tab filtering/presentation (IST-friendly timestamps, HH:MM:SS timers, numbered rows) and hardened container status roll-ups against legacy naive timestamps.
- Introduced `services.override_day_status()` along with `_normalise_datetimes` so manual overrides instantly cascade through day/week/phase aggregates without timezone errors.
- Rebuilt the Debian package via `scripts/build_linux_deb.sh` to confirm the PyInstaller + dpkg pipeline still lands the latest assets in `dist/linux/`.
- Completed the "version 1" QA sweep: audited every service/CLI/GUI flow touching timers, timezone math, filters, and overrides; spot-checked the 4-phase/52-week seed (13–17 tracked hours per week, 15 projects, 4 certifications) against the 70/30 core-to-trends plan; re-ran `poetry run pytest`, `poetry run ruff check`, and rebuilt/reinstalled the `.deb` to validate packaging end-to-end.
- Expanded the KPI set (boot times, bug counts, AI ops incident rates) so each phase tracks measurable outcomes, not just activities.
- Added `scripts/verify_seed.py` to assert structural integrity (phases/weeks/days/hours), enforce ≥3 tasks/resources per week, and confirm keyword coverage for foundations, RISC-V/ESP32-C3, Android Automotive HAL, and AI/MLOps observability before shipping seeds or installers.
- Introduced `Context.md` (this file) to describe the intent, architecture, and workflows for future collaborators or AI agents.

## Development workflow tips
- Install deps: `poetry install`.
- Generate/refresh seed data: `poetry run python scripts/generate_full_seed.py`.
- Reset + seed DB manually (optional): `poetry run python scripts/seed_roadmap.py data/roadmap_seed.json`.
- Run tests: `poetry run pytest`.
- Build Linux installer: `bash scripts/build_linux_deb.sh` (outputs `dist/linux/embedded-tracker_0.1.0_amd64.deb`).

With this context you can quickly judge how new features should slot into the data model, services layer, GUI tabs, or CLI surface without reverse-engineering the whole repo.