"""CLI for seeding the Embedded Tracker database from a JSON file."""

from __future__ import annotations

import argparse
from pathlib import Path

from embedded_tracker.seed import seed_from_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the Embedded Tracker database")
    parser.add_argument("seed_file", type=Path, help="Path to the JSON file containing roadmap data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_path: Path = args.seed_file
    phase_count = seed_from_file(seed_path)
    print(f"Seeded database with {phase_count} phase(s) from {seed_path}")


if __name__ == "__main__":
    main()
