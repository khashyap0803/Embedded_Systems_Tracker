#!/usr/bin/env python3
"""
Implement V6 Final Professional Audit Fixes:
1. Deduplicate metrics entries
2. Verify and fix stale resource URLs
3. Update week dates to proper sequence
"""

from datetime import date, timedelta
from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import (
    Phase, Week, DayPlan, Resource, Metric
)
from sqlmodel import select, col

init_db()

print("=" * 70)
print("🎓 IMPLEMENTING V6 FINAL PROFESSIONAL AUDIT FIXES")
print("=" * 70)

with session_scope() as session:
    
    # =========================================================================
    # FIX 1: Deduplicate Metrics Entries
    # =========================================================================
    print("\n--- FIX 1: Deduplicating Metrics Entries ---")
    
    metrics = session.exec(select(Metric).order_by(Metric.id)).all()
    seen = set()
    duplicates = []
    
    for m in metrics:
        key = (m.metric_type, m.value, m.phase_id)
        if key in seen:
            duplicates.append(m)
        else:
            seen.add(key)
    
    for dup in duplicates:
        session.delete(dup)
    
    session.commit()
    print(f"✅ Removed {len(duplicates)} duplicate metrics")
    
    # =========================================================================
    # FIX 2: Update Week Dates to Proper Sequence
    # =========================================================================
    print("\n--- FIX 2: Updating Week Dates to Proper Sequence ---")
    
    weeks = session.exec(select(Week).order_by(Week.number)).all()
    start_date = date(2025, 1, 6)  # Week 0 starts Jan 6, 2025
    
    updated_count = 0
    for w in weeks:
        expected_start = start_date + timedelta(weeks=w.number)
        expected_end = expected_start + timedelta(days=6)
        
        if w.start_date != expected_start or w.end_date != expected_end:
            w.start_date = expected_start
            w.end_date = expected_end
            session.add(w)
            updated_count += 1
    
    session.commit()
    print(f"✅ Updated dates for {updated_count} weeks")
    
    # =========================================================================
    # FIX 3: Verify and Flag Stale URLs
    # =========================================================================
    print("\n--- FIX 3: Checking Resource URLs ---")
    
    resources = session.exec(select(Resource)).all()
    
    # Known potentially stale URLs that should be updated
    stale_url_fixes = {
        "barrgroup.com/embedded-systems/": "https://www.amazon.in/Embedded-Coding-Standard-Michael-Barr/dp/1442164824",
        "st.com/stm32f7-series": "https://www.st.com/resource/en/reference_manual/rm0385-stm32f75xxx-and-stm32f74xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf",
        "nxp.com/docs/UM10204": "https://www.nxp.com/docs/en/user-guide/UM10204.pdf",
        "egghead.io": "https://www.youtube.com/results?search_query=embedded+systems+tutorial",
        "skillshare.com": "https://www.coursera.org/learn/embedded-systems-intro",
    }
    
    fixed_urls = 0
    for r in resources:
        if r.url:
            for pattern, replacement in stale_url_fixes.items():
                if pattern in r.url:
                    r.url = replacement
                    session.add(r)
                    fixed_urls += 1
                    break
    
    session.commit()
    print(f"✅ Fixed {fixed_urls} potentially stale URLs")
    
    # =========================================================================
    # VERIFY: Count all data
    # =========================================================================
    print("\n--- VERIFICATION: Final Data Counts ---")
    
    phases = session.exec(select(Phase)).all()
    weeks = session.exec(select(Week)).all()
    days = session.exec(select(DayPlan)).all()
    resources = session.exec(select(Resource)).all()
    metrics = session.exec(select(Metric)).all()
    
    print(f"  Phases:    {len(phases)}")
    print(f"  Weeks:     {len(weeks)}")
    print(f"  Days:      {len(days)}")
    print(f"  Resources: {len(resources)}")
    print(f"  Metrics:   {len(metrics)}")

print("\n" + "=" * 70)
print("✅ V6 FINAL PROFESSIONAL AUDIT FIXES IMPLEMENTED!")
print("=" * 70)
