"""Verification script for the roadmap seed.

This checks structural guarantees (phases, weeks, days, hours)
plus thematic coverage for foundations, RISC-V, Android/Automotive,
and AI/MLOps observability focus areas.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "roadmap_seed.json"

KEYWORD_FAMILIES = {
    "foundations": ["electronics", "logic", "breadboard", "uart", "digital", "c "],
    "riscv": ["risc-v", "esp32-c3", "esp32", "sifive", "hifive"],
    "android_auto": ["android", "automotive", "aaos", "hal", "aosp"],
    "ai_ops": ["tinyml", "mlops", "observability", "drift", "dashboard", "ai "],
}


def load_seed() -> dict:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    if "phases" not in data:
        raise SystemExit("Seed file missing 'phases' root key")
    return data


def check_structure(phases: list[dict]) -> list[str]:
    issues: list[str] = []
    week_counter = 0
    for phase in phases:
        weeks = phase.get("weeks", [])
        if not weeks:
            issues.append(f"Phase '{phase.get('name')}' has no weeks")
            continue
        for week in weeks:
            week_counter += 1
            tasks = week.get("tasks", [])
            resources = week.get("resources", [])
            days = week.get("days", [])
            if len(tasks) < 3:
                issues.append(f"Week {week['number']} has only {len(tasks)} tasks")
            if len(resources) < 3:
                issues.append(f"Week {week['number']} has only {len(resources)} resources")
            if len(days) != 7:
                issues.append(f"Week {week['number']} defines {len(days)} days instead of 7")
            for day in days:
                hours = day.get("hours", [])
                if day["number"] <= 5 and not hours:
                    issues.append(
                        f"Week {week['number']} day {day['number']} has no work hours"
                    )
                for hour in hours:
                    minutes = hour.get("estimated_minutes", 0)
                    if minutes <= 0:
                        issues.append(
                            f"Week {week['number']} day {day['number']} hour {hour['hour_number']}\n"
                            " has non-positive estimated minutes"
                        )
    if week_counter != 52:
        issues.append(f"Expected 52 weeks, found {week_counter}")
    return issues


def check_coverage(phases: list[dict]) -> dict[str, list[int]]:
    coverage: dict[str, list[int]] = defaultdict(list)
    for phase in phases:
        for week in phase.get("weeks", []):
            focus_blob = " ".join(
                [
                    week.get("focus", ""),
                    *[task.get("title", "") + " " + task.get("description", "") for task in week.get("tasks", [])],
                    *[
                        resource.get("title", "") + " " + resource.get("notes", "")
                        for resource in week.get("resources", [])
                    ],
                ]
            ).lower()
            for label, keywords in KEYWORD_FAMILIES.items():
                if any(keyword in focus_blob for keyword in keywords):
                    coverage[label].append(week["number"])
    return coverage


def main() -> None:
    seed = load_seed()
    phases = seed["phases"]
    print(f"Loaded seed with {len(phases)} phases")

    structure_issues = check_structure(phases)
    if structure_issues:
        print("\nStructural issues detected:")
        for issue in structure_issues:
            print(f" - {issue}")
    else:
        print("\nStructural integrity: PASS")

    coverage = check_coverage(phases)
    print("\nKeyword coverage summary:")
    for label, keywords in KEYWORD_FAMILIES.items():
        weeks = sorted(set(coverage.get(label, [])))
        indicator = "PASS" if weeks else "MISSING"
        print(f" - {label:13s} {indicator:8s} weeks={weeks if weeks else '[]'} (keywords: {', '.join(keywords)})")

    if structure_issues:
        raise SystemExit("Seed verification failed; see issues above")

    missing_labels = [label for label in KEYWORD_FAMILIES if not coverage.get(label)]
    if missing_labels:
        raise SystemExit("Missing keyword coverage for: " + ", ".join(missing_labels))

    print("\nAll verification checks passed.")


if __name__ == "__main__":
    main()
