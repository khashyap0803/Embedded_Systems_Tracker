#!/usr/bin/env python3
"""
HYPER-DETAILED DATA AUDIT SCRIPT
Verifies all data integrity for the Embedded Systems Tracker.
"""

import re
from collections import defaultdict
from datetime import date
from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import (
    Phase, Week, DayPlan, Task, Resource, Project, 
    Certification, Application, HardwareItem, Metric,
    ResourceType, TaskStatus
)
from sqlmodel import select, col

init_db()

print("=" * 80)
print("🔍 HYPER-DETAILED DATA AUDIT - Embedded Systems Tracker")
print("=" * 80)

issues = []
warnings = []

with session_scope() as session:
    
    # =========================================================================
    # SECTION 1: COUNT SUMMARY
    # =========================================================================
    print("\n📊 SECTION 1: DATA COUNTS")
    print("-" * 40)
    
    phases = session.exec(select(Phase)).all()
    weeks = session.exec(select(Week)).all()
    days = session.exec(select(DayPlan)).all()
    tasks = session.exec(select(Task)).all()
    resources = session.exec(select(Resource)).all()
    projects = session.exec(select(Project)).all()
    certs = session.exec(select(Certification)).all()
    apps = session.exec(select(Application)).all()
    hardware = session.exec(select(HardwareItem)).all()
    metrics = session.exec(select(Metric)).all()
    
    print(f"Phases:        {len(phases)}")
    print(f"Weeks:         {len(weeks)}")
    print(f"Days:          {len(days)}")
    print(f"Tasks:         {len(tasks)}")
    print(f"Resources:     {len(resources)}")
    print(f"Projects:      {len(projects)}")
    print(f"Certifications:{len(certs)}")
    print(f"Applications:  {len(apps)}")
    print(f"Hardware:      {len(hardware)}")
    print(f"Metrics:       {len(metrics)}")
    
    # =========================================================================
    # SECTION 2: WEEK SEQUENCING & GAPS
    # =========================================================================
    print("\n📅 SECTION 2: WEEK SEQUENCING")
    print("-" * 40)
    
    week_numbers = sorted([w.number for w in weeks])
    print(f"Week range: {min(week_numbers)} to {max(week_numbers)}")
    
    # Check for gaps
    expected = set(range(min(week_numbers), max(week_numbers) + 1))
    actual = set(week_numbers)
    gaps = expected - actual
    duplicates = [n for n in week_numbers if week_numbers.count(n) > 1]
    
    if gaps:
        issues.append(f"Missing weeks: {sorted(gaps)}")
        print(f"❌ GAPS: {sorted(gaps)}")
    else:
        print("✅ No gaps in week sequence")
    
    if duplicates:
        issues.append(f"Duplicate weeks: {set(duplicates)}")
        print(f"❌ DUPLICATES: {set(duplicates)}")
    else:
        print("✅ No duplicate weeks")
    
    # Week 0 check
    week0 = session.exec(select(Week).where(Week.number == 0)).first()
    if week0:
        print(f"✅ Week 0 exists: {week0.focus[:50]}...")
    else:
        issues.append("Week 0 (Pre-requisites) is MISSING!")
        print("❌ Week 0 is MISSING!")
    
    # =========================================================================
    # SECTION 3: PHASE-WEEK ALIGNMENT
    # =========================================================================
    print("\n🔗 SECTION 3: PHASE-WEEK ALIGNMENT")
    print("-" * 40)
    
    for phase in phases:
        phase_weeks = [w for w in weeks if w.phase_id == phase.id]
        week_nums = sorted([w.number for w in phase_weeks])
        print(f"{phase.name}: Weeks {week_nums[0] if week_nums else 'N/A'}-{week_nums[-1] if week_nums else 'N/A'} ({len(phase_weeks)} weeks)")
    
    # =========================================================================
    # SECTION 4: RESOURCE URL VALIDATION
    # =========================================================================
    print("\n🔗 SECTION 4: RESOURCE URL VALIDATION")
    print("-" * 40)
    
    url_issues = []
    for r in resources:
        if not r.url:
            url_issues.append(f"Resource '{r.title}' has NO URL")
        elif not r.url.startswith(("http://", "https://")):
            url_issues.append(f"Resource '{r.title}' has invalid URL: {r.url[:30]}")
    
    if url_issues:
        print(f"❌ {len(url_issues)} URL issues found")
        for issue in url_issues[:5]:
            print(f"   - {issue}")
        if len(url_issues) > 5:
            print(f"   ... and {len(url_issues) - 5} more")
        issues.extend(url_issues)
    else:
        print(f"✅ All {len(resources)} resources have valid URL format")
    
    # =========================================================================
    # SECTION 5: 50+ LPA SKILL COVERAGE
    # =========================================================================
    print("\n💼 SECTION 5: 50+ LPA SKILL COVERAGE")
    print("-" * 40)
    
    required_skills = {
        "ARM Cortex": False,
        "FreeRTOS": False,
        "Zephyr": False,
        "I2C": False,
        "SPI": False,
        "UART": False,
        "CAN": False,
        "USB": False,
        "BLE": False,
        "Ethernet": False,
        "MQTT": False,
        "TinyML": False,
        "Linux": False,
        "Device Tree": False,
        "Yocto": False,
        "AUTOSAR": False,
        "ISO 26262": False,
        "MISRA": False,
        "Bootloader": False,
        "DMA": False,
        "Power Management": False,
    }
    
    # Search in weeks, days, tasks, resources
    all_text = ""
    for w in weeks:
        all_text += f" {w.focus or ''}"
    for d in days:
        all_text += f" {d.focus or ''} {d.notes or ''}"
    for t in tasks:
        all_text += f" {t.title or ''} {t.description or ''} {t.ai_prompt or ''}"
    for r in resources:
        all_text += f" {r.title or ''} {r.notes or ''}"
    
    all_text = all_text.lower()
    
    for skill in required_skills:
        if skill.lower() in all_text:
            required_skills[skill] = True
    
    covered = sum(1 for v in required_skills.values() if v)
    total = len(required_skills)
    coverage_pct = (covered / total) * 100
    
    print(f"Coverage: {covered}/{total} ({coverage_pct:.0f}%)")
    
    missing = [k for k, v in required_skills.items() if not v]
    if missing:
        print(f"⚠️ Missing skills: {', '.join(missing)}")
        warnings.append(f"Missing skills for 50+ LPA: {', '.join(missing)}")
    else:
        print("✅ All critical skills covered")
    
    # =========================================================================
    # SECTION 6: FORBIDDEN CONTENT CHECK
    # =========================================================================
    print("\n🚫 SECTION 6: FORBIDDEN CONTENT CHECK")
    print("-" * 40)
    
    forbidden = ["HTML", "CSS", "JavaScript", "React", "Vue", "Angular", "Django", "Flask", 
                 "DaVinci", "Premiere", "Photoshop", "Illustrator"]
    
    forbidden_found = []
    for term in forbidden:
        if term.lower() in all_text:
            # Find where it appears
            forbidden_found.append(term)
    
    if forbidden_found:
        print(f"⚠️ Potentially forbidden terms found: {', '.join(forbidden_found)}")
        # Check if in acceptable context (like Week 55 portfolio)
        warnings.append(f"Review context of: {', '.join(forbidden_found)}")
    else:
        print("✅ No forbidden content detected")
    
    # =========================================================================
    # SECTION 7: HARDWARE BOM CHECK
    # =========================================================================
    print("\n🔧 SECTION 7: HARDWARE BOM CHECK")
    print("-" * 40)
    
    required_hw = ["STM32", "Nucleo", "Oscilloscope", "Logic Analyzer", "Raspberry Pi"]
    hw_names = [h.name.lower() for h in hardware]
    hw_text = " ".join(hw_names)
    
    for item in required_hw:
        if item.lower() in hw_text:
            print(f"✅ {item} found in BOM")
        else:
            print(f"⚠️ {item} NOT found in BOM")
            warnings.append(f"Hardware BOM missing: {item}")
    
    # =========================================================================
    # SECTION 8: INTERVIEW PREP CHECK
    # =========================================================================
    print("\n🎯 SECTION 8: INTERVIEW PREP CHECK")
    print("-" * 40)
    
    interview_weeks = [w for w in weeks if "interview" in (w.focus or "").lower()]
    if interview_weeks:
        print(f"✅ Found {len(interview_weeks)} interview prep week(s):")
        for w in interview_weeks:
            print(f"   Week {w.number}: {w.focus[:50]}...")
    else:
        issues.append("No interview preparation weeks found!")
        print("❌ No interview prep weeks found!")
    
    # =========================================================================
    # SECTION 9: LINUX COVERAGE CHECK
    # =========================================================================
    print("\n🐧 SECTION 9: LINUX COVERAGE CHECK")
    print("-" * 40)
    
    linux_weeks = [w for w in weeks if "linux" in (w.focus or "").lower()]
    if linux_weeks:
        print(f"✅ Found {len(linux_weeks)} Linux-related week(s):")
        for w in linux_weeks:
            print(f"   Week {w.number}: {w.focus[:50]}...")
    else:
        issues.append("No Embedded Linux weeks found!")
        print("❌ No Linux weeks found!")
    
    # =========================================================================
    # SECTION 10: PROTOCOL COVERAGE
    # =========================================================================
    print("\n📡 SECTION 10: PROTOCOL COVERAGE")
    print("-" * 40)
    
    protocols = {
        "I2C": False, "SPI": False, "UART": False, 
        "CAN": False, "LIN": False, "USB": False,
        "BLE": False, "MQTT": False, "Ethernet": False
    }
    
    week_focuses = " ".join([w.focus or "" for w in weeks]).lower()
    
    for proto in protocols:
        if proto.lower() in week_focuses:
            protocols[proto] = True
            print(f"✅ {proto} covered")
        else:
            print(f"⚠️ {proto} NOT explicitly in week focus")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("📋 AUDIT SUMMARY")
    print("=" * 80)
    
    if not issues:
        print("\n✅✅✅ NO CRITICAL ISSUES FOUND ✅✅✅")
    else:
        print(f"\n❌ CRITICAL ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"   - {issue}")
    
    if warnings:
        print(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"   - {warn}")
    
    # Calculate final score
    score = 10.0
    score -= len(issues) * 0.5
    score -= len(warnings) * 0.1
    score = max(0, min(10, score))
    
    print(f"\n📊 DATA QUALITY SCORE: {score:.1f}/10")
    
    if score >= 9.0:
        print("🏆 VERDICT: PLATINUM TIER - Ready for production!")
    elif score >= 8.0:
        print("🥇 VERDICT: GOLD TIER - Minor improvements suggested")
    elif score >= 7.0:
        print("🥈 VERDICT: SILVER TIER - Needs attention")
    else:
        print("🥉 VERDICT: BRONZE TIER - Significant work needed")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
