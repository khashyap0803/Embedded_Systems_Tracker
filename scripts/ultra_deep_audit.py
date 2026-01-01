#!/usr/bin/env python3
"""
ULTRA-COMPREHENSIVE DATA AUDIT
Checks ALL high, medium, and low severity issues in:
- audit_data/ (CSV exports)
- embedded_tracker/data/ (JSON files)
"""

import csv
import json
import os
import re
from pathlib import Path
from datetime import datetime, date
from collections import Counter, defaultdict

AUDIT_DIR = Path("/home/nani/Videos/embedded-tracker/audit_data")
DATA_DIR = Path("/home/nani/Videos/embedded-tracker/embedded_tracker/data")

issues = {"high": [], "medium": [], "low": []}
stats = {}

def add_issue(severity, category, message):
    issues[severity].append((category, message))

print("=" * 80)
print("🔬 ULTRA-COMPREHENSIVE DATA AUDIT")
print("=" * 80)

# =============================================================================
# LOAD ALL CSV DATA
# =============================================================================
print("\n📂 Loading CSV Data from audit_data/...")

def load_csv(filename):
    path = AUDIT_DIR / filename
    if not path.exists():
        add_issue("high", "MISSING_FILE", f"{filename} not found")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

phases = load_csv("01_phases.csv")
weeks = load_csv("02_weeks.csv")
days = load_csv("03_days.csv")
tasks = load_csv("04_tasks.csv")
resources = load_csv("05_resources.csv")
projects = load_csv("06_projects.csv")
certifications = load_csv("07_certifications.csv")
applications = load_csv("08_applications.csv")
hardware = load_csv("09_hardware.csv")
metrics = load_csv("10_metrics.csv")

stats["phases"] = len(phases)
stats["weeks"] = len(weeks)
stats["days"] = len(days)
stats["tasks"] = len(tasks)
stats["resources"] = len(resources)
stats["projects"] = len(projects)
stats["certifications"] = len(certifications)
stats["applications"] = len(applications)
stats["hardware"] = len(hardware)
stats["metrics"] = len(metrics)

print(f"  Loaded: {sum(stats.values())} total rows")

# =============================================================================
# LOAD JSON DATA
# =============================================================================
print("\n📂 Loading JSON Data from embedded_tracker/data/...")

json_files = {}
for json_file in DATA_DIR.glob("*.json"):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_files[json_file.name] = json.load(f)
        print(f"  ✓ {json_file.name}")
    except Exception as e:
        add_issue("high", "JSON_ERROR", f"Failed to parse {json_file.name}: {e}")

# =============================================================================
# SECTION 1: PHASE CHECKS
# =============================================================================
print("\n" + "=" * 80)
print("📊 SECTION 1: PHASE VALIDATION")
print("=" * 80)

phase_ids = set()
for p in phases:
    pid = p.get("ID")
    name = p.get("Name", "")
    
    # Check for empty names
    if not name or name.strip() == "":
        add_issue("high", "EMPTY_NAME", f"Phase {pid} has empty name")
    
    # Check for duplicates
    if pid in phase_ids:
        add_issue("high", "DUPLICATE", f"Duplicate phase ID: {pid}")
    phase_ids.add(pid)

print(f"  ✓ {len(phases)} phases validated")

# =============================================================================
# SECTION 2: WEEK CHECKS
# =============================================================================
print("\n" + "=" * 80)
print("📅 SECTION 2: WEEK VALIDATION")
print("=" * 80)

week_numbers = []
week_ids = set()
for w in weeks:
    wid = w.get("ID")
    wnum = int(w.get("Week Number", -1))
    focus = w.get("Focus", "")
    phase_id = w.get("Phase ID")
    start_date = w.get("Start Date")
    
    week_numbers.append(wnum)
    
    # Check for empty focus
    if not focus or focus.strip() == "" or len(focus) < 10:
        add_issue("medium", "SHORT_FOCUS", f"Week {wnum} has very short focus: '{focus[:30]}'")
    
    # Check for duplicate week numbers
    if wnum in week_ids:
        add_issue("high", "DUPLICATE_WEEK", f"Duplicate week number: {wnum}")
    week_ids.add(wnum)
    
    # Check phase linkage
    if not phase_id or phase_id == "None":
        add_issue("high", "ORPHAN_WEEK", f"Week {wnum} not linked to any phase")
    
    # Check date format
    if start_date and start_date != "None":
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except:
            add_issue("low", "DATE_FORMAT", f"Week {wnum} has invalid date format: {start_date}")

# Check for gaps in week sequence
week_numbers.sort()
if week_numbers:
    expected = list(range(week_numbers[0], week_numbers[-1] + 1))
    gaps = set(expected) - set(week_numbers)
    if gaps:
        add_issue("high", "WEEK_GAPS", f"Missing weeks: {sorted(gaps)}")

print(f"  ✓ {len(weeks)} weeks validated")
print(f"  Week range: {min(week_numbers)} to {max(week_numbers)}")

# =============================================================================
# SECTION 3: DAY CHECKS
# =============================================================================
print("\n" + "=" * 80)
print("📆 SECTION 3: DAY VALIDATION")
print("=" * 80)

days_per_week = Counter()
for d in days:
    week_id = d.get("Week ID")
    day_num = int(d.get("Day Number", 0))
    focus = d.get("Focus", "")
    
    days_per_week[week_id] += 1
    
    # Check for empty focus
    if not focus or len(focus) < 5:
        add_issue("low", "SHORT_DAY_FOCUS", f"Day {day_num} in Week {d.get('Week Number')} has short focus")
    
    # Check day number validity
    if day_num < 1 or day_num > 7:
        add_issue("medium", "INVALID_DAY_NUM", f"Day number {day_num} out of range (1-7)")

# Check weeks with unusual day counts
for week_id, count in days_per_week.items():
    if count != 7 and count != 6:  # Most weeks should have 6-7 days
        add_issue("low", "DAY_COUNT", f"Week ID {week_id} has {count} days (expected 6-7)")

print(f"  ✓ {len(days)} days validated")
print(f"  Average days per week: {len(days) / len(weeks):.1f}")

# =============================================================================
# SECTION 4: TASK CHECKS
# =============================================================================
print("\n" + "=" * 80)
print("📋 SECTION 4: TASK VALIDATION")
print("=" * 80)

tasks_with_ai_prompt = 0
tasks_without_ai = []
task_statuses = Counter()

for t in tasks:
    tid = t.get("ID")
    title = t.get("Title", "")
    ai_prompt = t.get("AI Prompt", "")
    status = t.get("Status", "pending")
    
    task_statuses[status] += 1
    
    # Check for AI prompt
    if ai_prompt and len(ai_prompt) > 10:
        tasks_with_ai_prompt += 1
    else:
        tasks_without_ai.append(title[:50])
    
    # Check for empty titles
    if not title or len(title) < 5:
        add_issue("medium", "SHORT_TITLE", f"Task {tid} has short title: '{title}'")

if tasks_without_ai:
    add_issue("low", "MISSING_AI_PROMPT", f"{len(tasks_without_ai)} tasks without AI prompts")

print(f"  ✓ {len(tasks)} tasks validated")
print(f"  With AI prompts: {tasks_with_ai_prompt}/{len(tasks)} ({100*tasks_with_ai_prompt/len(tasks):.1f}%)")
print(f"  Status distribution: {dict(task_statuses)}")

# =============================================================================
# SECTION 5: RESOURCE URL VALIDATION (DETAILED)
# =============================================================================
print("\n" + "=" * 80)
print("🔗 SECTION 5: RESOURCE URL VALIDATION")
print("=" * 80)

resource_types = Counter()
url_domains = Counter()
broken_url_patterns = []

# Known bad URL patterns
bad_patterns = [
    "example.com", "placeholder", "xxx", "test.com", 
    "localhost", "127.0.0.1", ".local", "changeme"
]

for r in resources:
    title = r.get("Title", "")
    url = r.get("URL", "")
    rtype = r.get("Type", "other")
    
    resource_types[rtype] += 1
    
    # Extract domain
    if url.startswith("http"):
        domain = url.split("/")[2] if len(url.split("/")) > 2 else ""
        url_domains[domain] += 1
    
    # Check for placeholder URLs
    if not url or url == "None" or len(url) < 10:
        add_issue("medium", "MISSING_URL", f"Resource '{title[:40]}' has no valid URL")
    
    # Check for bad patterns
    for pattern in bad_patterns:
        if pattern in url.lower():
            add_issue("high", "BAD_URL", f"Resource '{title[:40]}' has placeholder URL: {url[:50]}")
            break
    
    # Check URL format
    if url and not url.startswith(("http://", "https://")):
        add_issue("low", "URL_FORMAT", f"Resource '{title[:40]}' URL doesn't start with http(s)")

print(f"  ✓ {len(resources)} resources validated")
print(f"  Types: {dict(resource_types)}")
print(f"  Top domains: {url_domains.most_common(5)}")

# =============================================================================
# SECTION 6: PROJECT VALIDATION
# =============================================================================
print("\n" + "=" * 80)
print("🚀 SECTION 6: PROJECT VALIDATION")
print("=" * 80)

for p in projects:
    name = p.get("Name", "")
    repo = p.get("Repo URL", "")
    demo = p.get("Demo URL", "")
    status = p.get("Status", "")
    
    # Check for missing repo URLs
    if not repo or repo == "None" or len(repo) < 10:
        add_issue("low", "MISSING_REPO", f"Project '{name}' has no repo URL")
    
    # Check for github-specific validation
    if repo and "github.com" in repo.lower():
        if not re.match(r'https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+', repo):
            add_issue("low", "INVALID_GITHUB", f"Project '{name}' has unusual GitHub URL format")

print(f"  ✓ {len(projects)} projects validated")

# =============================================================================
# SECTION 7: CERTIFICATION VALIDATION
# =============================================================================
print("\n" + "=" * 80)
print("🎓 SECTION 7: CERTIFICATION VALIDATION")
print("=" * 80)

for c in certifications:
    name = c.get("Name", "")
    provider = c.get("Provider", "")
    
    if not provider or provider == "None":
        add_issue("low", "MISSING_PROVIDER", f"Certification '{name}' missing provider")

print(f"  ✓ {len(certifications)} certifications validated")

# =============================================================================
# SECTION 8: APPLICATION VALIDATION
# =============================================================================
print("\n" + "=" * 80)
print("💼 SECTION 8: JOB APPLICATION VALIDATION")
print("=" * 80)

target_companies = []
for a in applications:
    company = a.get("Company", "")
    role = a.get("Role", "")
    target_companies.append(company)
    
    if not role or role == "None":
        add_issue("low", "MISSING_ROLE", f"Application to '{company}' missing role")

print(f"  ✓ {len(applications)} applications validated")
print(f"  Target companies: {', '.join(target_companies)}")

# =============================================================================
# SECTION 9: HARDWARE VALIDATION
# =============================================================================
print("\n" + "=" * 80)
print("🔧 SECTION 9: HARDWARE VALIDATION")
print("=" * 80)

hw_categories = Counter()
essential_hw = ["STM32", "Nucleo", "ESP32", "Oscilloscope", "Logic Analyzer", "Multimeter"]
found_essential = []

for h in hardware:
    name = h.get("Name", "")
    category = h.get("Category", "other")
    hw_categories[category] += 1
    
    for essential in essential_hw:
        if essential.lower() in name.lower():
            found_essential.append(essential)

missing_essential = set(essential_hw) - set(found_essential)
if missing_essential:
    add_issue("medium", "MISSING_HW", f"Essential hardware missing: {missing_essential}")

print(f"  ✓ {len(hardware)} hardware items validated")
print(f"  Categories: {dict(hw_categories)}")

# =============================================================================
# SECTION 10: METRICS VALIDATION
# =============================================================================
print("\n" + "=" * 80)
print("📈 SECTION 10: METRICS VALIDATION")
print("=" * 80)

metric_types = Counter()
for m in metrics:
    mtype = m.get("Type", "")
    metric_types[mtype] += 1

print(f"  ✓ {len(metrics)} metrics validated")
print(f"  Types: {dict(metric_types)}")

# =============================================================================
# SECTION 11: CONTENT QUALITY CHECKS
# =============================================================================
print("\n" + "=" * 80)
print("📝 SECTION 11: CONTENT QUALITY CHECKS")
print("=" * 80)

# Check for forbidden content
forbidden_terms = ["web development", "react", "angular", "vue.js", "node.js", 
                   "video editing", "davinci resolve", "premiere", "photoshop",
                   "wordpress", "shopify", "seo optimization"]

for w in weeks:
    focus = w.get("Focus", "").lower()
    for term in forbidden_terms:
        if term in focus:
            add_issue("high", "FORBIDDEN_CONTENT", f"Week {w.get('Week Number')} contains '{term}'")

# Check for 50+ LPA skills coverage
required_skills = [
    "RTOS", "FreeRTOS", "Zephyr", "CAN", "LIN", "I2C", "SPI", "UART", 
    "USB", "BLE", "Bluetooth", "MQTT", "Ethernet", "TCP", "Linux", 
    "Yocto", "AUTOSAR", "ISO 26262", "Safety", "Bootloader", "DMA",
    "ARM", "Cortex", "STM32", "TinyML", "Edge AI"
]

all_focus = " ".join([w.get("Focus", "") for w in weeks]).lower()
found_skills = []
missing_skills = []

for skill in required_skills:
    if skill.lower() in all_focus:
        found_skills.append(skill)
    else:
        missing_skills.append(skill)

if missing_skills:
    add_issue("low", "SKILL_GAP", f"Skills not explicitly in week focus: {missing_skills}")

print(f"  Skills coverage: {len(found_skills)}/{len(required_skills)}")

# =============================================================================
# SECTION 12: JSON DATA VALIDATION
# =============================================================================
print("\n" + "=" * 80)
print("📄 SECTION 12: JSON DATA VALIDATION")
print("=" * 80)

if "roadmap_seed.json" in json_files:
    roadmap = json_files["roadmap_seed.json"]
    if "phases" in roadmap:
        print(f"  roadmap_seed.json: {len(roadmap['phases'])} phases")
    else:
        add_issue("medium", "JSON_STRUCTURE", "roadmap_seed.json missing 'phases' key")

if "hardware_bom.json" in json_files:
    bom = json_files["hardware_bom.json"]
    if isinstance(bom, list):
        print(f"  hardware_bom.json: {len(bom)} categories")
    elif isinstance(bom, dict):
        total_items = sum(len(v) if isinstance(v, list) else 1 for v in bom.values())
        print(f"  hardware_bom.json: {total_items} items")

if "hardware_inventory.json" in json_files:
    print(f"  hardware_inventory.json: loaded")

if "pre_week1_checklist.json" in json_files:
    print(f"  pre_week1_checklist.json: loaded")

if "system_specs.json" in json_files:
    print(f"  system_specs.json: loaded")

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print("📋 AUDIT SUMMARY")
print("=" * 80)

print(f"\n📊 DATA STATISTICS:")
for k, v in stats.items():
    print(f"  {k.capitalize():15} {v:>5}")
print(f"  {'TOTAL':15} {sum(stats.values()):>5}")

high_count = len(issues["high"])
medium_count = len(issues["medium"])
low_count = len(issues["low"])
total_issues = high_count + medium_count + low_count

print(f"\n🚨 ISSUES FOUND:")
print(f"  🔴 HIGH:   {high_count}")
print(f"  🟡 MEDIUM: {medium_count}")
print(f"  🟢 LOW:    {low_count}")
print(f"  TOTAL:    {total_issues}")

if issues["high"]:
    print(f"\n🔴 HIGH SEVERITY ISSUES (Must Fix):")
    for cat, msg in issues["high"][:10]:
        print(f"  [{cat}] {msg}")

if issues["medium"]:
    print(f"\n🟡 MEDIUM SEVERITY ISSUES (Should Fix):")
    for cat, msg in issues["medium"][:10]:
        print(f"  [{cat}] {msg}")

if issues["low"]:
    print(f"\n🟢 LOW SEVERITY ISSUES (Nice to Fix):")
    for cat, msg in issues["low"][:10]:
        print(f"  [{cat}] {msg}")

# Calculate score
if total_issues == 0:
    score = 10.0
else:
    penalty = high_count * 1.0 + medium_count * 0.3 + low_count * 0.1
    score = max(0, 10.0 - penalty)

print(f"\n📊 DATA QUALITY SCORE: {score:.1f}/10")

if score >= 9.5:
    print("🏆 VERDICT: PLATINUM TIER - Ready for production!")
elif score >= 8.5:
    print("🥇 VERDICT: GOLD TIER - Minor fixes needed")
elif score >= 7.0:
    print("🥈 VERDICT: SILVER TIER - Some fixes recommended")
else:
    print("🥉 VERDICT: BRONZE TIER - Significant fixes required")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)

# Save issues to file
issues_file = AUDIT_DIR / "AUDIT_ISSUES.json"
with open(issues_file, 'w') as f:
    json.dump(issues, f, indent=2)
print(f"\n📁 Issues saved to: {issues_file}")
