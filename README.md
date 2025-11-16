# Embedded Tracker

Embedded Tracker is a cross-platform personal dashboard designed to help you execute the Embedded Systems Mastery roadmap between October 2025 and October 2026. The project now ships with both a rich CLI and a PySide6 desktop interface driven by a shared SQLModel data layer.

## Features (Current & Planned)
- ✅ SQLModel data schema for phases, weeks, tasks, resources, projects, certifications, applications, and metrics.
- ✅ Auto-seeding that imports the roadmap JSON on first launch via shared helpers in `embedded_tracker.seed`.
- ✅ Phase 1 now devotes its first eight weeks to electronics basics, digital logic, C mastery, and UART/I2C/SPI drills before progressing to advanced bring-up work.
- ✅ Phase 2 injects open RISC-V + ESP32-C3 bring-up, dual-stack connectivity labs, and Android companion provisioning flows on top of the Zephyr/FreeRTOS stack.
- ✅ Phase 3/4 add Android Automotive HAL integration, AAOS security operations, AI observability weeks, and KPI metrics (boot times, bug counts, incident rates) so later work mirrors production readiness.
- ✅ `scripts/verify_seed.py` enforces structural integrity (phases/weeks/days/hours) and keyword coverage for foundations, RISC-V, Android/Automotive, and AI/MLOps themes before packaging.
- ✅ Rich-powered CLI (`embedded-tracker list`, `embedded-tracker projects`, `embedded-tracker certifications`, etc.) to inspect roadmap progress from the terminal.
- ✅ PySide6 desktop GUI with CRUD management tabs, filters, and shared persistence.
- 🔄 Upcoming: analytics dashboards, AI prompt panels, GitHub/Notion sync, secure keyring storage.

## Getting Started

### Prerequisites
- Python 3.12 managed via `pyenv` (recommended).
- `poetry` for environment and dependency management.

### Setup
```bash
pyenv install 3.12.1
pyenv local 3.12.1
python -m pip install --upgrade pip
pip install poetry
poetry install
```

### Seed the Database
The app seeds itself automatically on first launch (both CLI and GUI call `ensure_seed_data()`), pulling from `data/roadmap_seed.json` when running from source or the packaged copy under `embedded_tracker/data/roadmap_seed.json` when installed.

To refresh the roadmap manually (after editing the JSON or generating a new one), run:

```bash
poetry run python scripts/seed_roadmap.py data/roadmap_seed.json
```

### Regenerate the curated roadmap
`scripts/generate_full_seed.py` produces the 52-week plan (including projects, certifications, applications, and metrics) and writes it to both the repo `data/` folder and the packaged `embedded_tracker/data/` directory. Rerun it whenever you tweak the template:

```bash
poetry run python scripts/generate_full_seed.py
```

### Verify the roadmap quality
Run the automated audit before packaging to guarantee every phase/week/day/hour is populated and key themes stay represented:

```bash
poetry run python scripts/verify_seed.py
```

The script checks for:
- 52 total weeks across 4 phases, each with ≥3 tasks/resources.
- Weekday schedules that include hour-level work blocks.
- Coverage hits for foundational electronics, open RISC-V/ESP32-C3 bring-up, Android/Automotive HAL work, and AI/MLOps observability.

### Use the CLI
```bash
poetry run embedded-tracker list --week 1
poetry run embedded-tracker projects --status in_progress
poetry run embedded-tracker certifications --status planned
poetry run embedded-tracker metrics --metric-type hours_logged
```

### Launch the GUI
```bash
poetry run embedded-tracker-gui
# or
poetry run python main.py
```

The first launch will create a per-user data directory in:

- `%LOCALAPPDATA%\EmbeddedTracker` on Windows
- `~/Library/Application Support/EmbeddedTracker` on macOS
- `$XDG_DATA_HOME/embedded-tracker` (or `~/.local/share/embedded-tracker`) on Linux

### Package the App
- **Windows**: run `scripts/build_windows_exe.ps1` from PowerShell on a Windows host to generate a single-file `EmbeddedTracker.exe` (PyInstaller will bundle the packaged seed JSON, so first launch is still populated).
- **Ubuntu/Debian**: run `scripts/build_linux_deb.sh` on a Linux host with `dpkg-deb` installed to produce `dist/linux/embedded-tracker_0.1.0_amd64.deb`.

Both scripts call `pyinstaller`, so ensure you installed dev dependencies via `poetry install --with dev`.

## Project Structure
```
embedded-tracker/
├── embedded_tracker/
│   ├── __init__.py
│   ├── cli.py
│   ├── db.py
│   ├── seed.py
│   ├── gui/
│   │   ├── __init__.py
│   │   └── main_window.py
│   ├── models.py
│   └── services.py
│   └── data/
│       └── roadmap_seed.json
├── data/
│   └── roadmap_seed.json
├── scripts/
│   ├── build_linux_deb.sh
│   ├── build_windows_exe.ps1
│   ├── generate_full_seed.py
│   └── seed_roadmap.py
├── tests/
│   └── test_models.py
├── main.py
├── pyproject.toml
└── README.md
```

## Next Steps
1. Add analytics dashboards and timeline visualisations to the GUI.
2. Integrate AI prompt templates, keyring storage, and sync services.
3. Harden packaging workflows (icons, auto-updaters, notarisation/signing).
