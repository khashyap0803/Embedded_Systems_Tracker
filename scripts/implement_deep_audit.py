#!/usr/bin/env python3
"""
Implement Deep Audit Recommendations:
1. Fix URLs
2. Add Phase 3.5 (Linux)
3. Add Protocols (FreeRTOS, USB, Net)
4. Update Hardware
5. Shift Weeks to accommodate new content
"""

from datetime import date, timedelta
from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import (
    Phase, Week, DayPlan, Task, Resource, HardwareItem, 
    ResourceType, TaskStatus, HardwareStatus
)
from sqlmodel import select, col

init_db()

def get_week_by_num(session, num):
    return session.exec(select(Week).where(Week.number == num)).first()

def shift_weeks(session, start_num, shift_amount):
    print(f"Adding +{shift_amount} to weeks >= {start_num}...")
    # Get weeks in descending order to avoid constraint issues during update if uniq constraint exists
    weeks = session.exec(select(Week).where(Week.number >= start_num).order_by(col(Week.number).desc())).all()
    for w in weeks:
        w.number += shift_amount
        # Shift start/end dates roughly (optional but good for visuals)
        if w.start_date: w.start_date += timedelta(weeks=shift_amount)
        if w.end_date: w.end_date += timedelta(weeks=shift_amount)
        session.add(w)
    session.commit()
    print(f"Shifted {len(weeks)} weeks.")

# ============================================================================
# MAIN MIGRATION
# ============================================================================

with session_scope() as session:
    print("=== STARTING DEEP AUDIT IMPLEMENTATION ===")

    # 1. FIX URLS (Priority 1) -> ALREADY DONE
    # -----------------------------------------------------
    # print("\n--- Fixing Broken URLs ---")
    # ... skipped ...

    # 2. WEEK SHIFTING STRATEGY -> ALREADY DONE
    # -----------------------------------------------------
    # print("\n--- Shifting Weeks ---")
    # shift_weeks(session, 35, 2)
    # shift_weeks(session, 47, 4)
    
    # 3. ADD MISSING PROTOCOLS -> ALREADY DONE
    # -----------------------------------------------------
    # print("\n--- Adding Protocols (FreeRTOS, USB, Networking) ---")
    
    # 4. ADD PHASE 3.5 (LINUX)
    # -----------------------------------------------------
    print("\n--- Adding Phase 3.5: Embedded Linux Bridge ---")
    
    p35 = session.exec(select(Phase).where(Phase.name.contains("Phase 3.5"))).first()
    if not p35:
        p35 = Phase(name="Phase 3.5 – Embedded Linux Bridge", description="Bridge from bare-metal to Linux: Kernel modules, Device Trees, and Drivers.", start_date=date(2025, 10, 15))
        session.add(p35)
        session.commit()
        session.refresh(p35)
    
    # Week 47-50 (Slots created by shift)
    linux_weeks = [
        (47, "Week 47 – Linux Kernel Modules & Build System (Kbuild)", [
            "Linux Kernel Architecture", "Loadable Kernel Modules (LKM)", "Kbuild & Makefiles",
            "Module Parameters & Exports", "Kernel Symbols & System Map", "Cross-Compilation for ARM", "Hello World Module"
        ]),
        (48, "Week 48 – Device Tree & Hardware Description", [
            "Device Tree Syntax (DTS/DTB)", "Nodes, Properties, & Phandles", "DT Overlays",
            "Pinctrl & GPIO in DT", "Debugging DT (fdtdump)", "Sysfs & Procfs exploration", "Board Bring-up Basics"
        ]),
        (49, "Week 49 – Yocto Project & Buildroot Basics", [
            "Build Systems Overview", "Bitbake & Recipes", "Layers & Meta-data",
            "Creating Custom Image", "SDK Generation", "Root Filesystem Structure", "Patching Kernel in Yocto"
        ]),
        (50, "Week 50 – Linux Character Device Drivers", [
            "Char Driver Structure (open/read/write)", "Major/Minor Numbers", "File Operations (cdev)",
            "User-Kernel Data Transfer (copy_to_user)", "Blocking IO & Wait Queues", "Platform Drivers", "Project: SPI/I2C Linux Driver"
        ])
    ]
    
    base_date = date(2025, 10, 20)
    for w_num, w_focus, days_list in linux_weeks:
        # Check if week exists to avoid duplication if re-run
        existing = session.exec(select(Week).where(Week.number == w_num)).first()
        if existing and "Linux" in existing.focus:
            print(f"Week {w_num} already exists.")
            wk = existing
        else:
            # Use timedelta for safe date math
            wk_start = base_date + timedelta(weeks=(w_num-47))
            wk = Week(number=w_num, phase_id=p35.id, focus=w_focus, start_date=wk_start)
            session.add(wk)
            session.commit()
            session.refresh(wk)
            for i, d_focus in enumerate(days_list, 1):
                session.add(DayPlan(number=i, focus=d_focus, week_id=wk.id))
            
            # Add a resource
            if w_num == 47:
                session.add(Resource(title="Linux Device Drivers 3 (LDD3)", type=ResourceType.BOOK, url="https://lwn.net/Kernel/LDD3/", week_id=wk.id))
            if w_num == 48:
                session.add(Resource(title="Device Tree for Dummies", type=ResourceType.DOCS, url="https://events.static.linuxfound.org/sites/events/files/slides/petazzoni-device-tree-dummies.pdf", week_id=wk.id))
            if w_num == 49:
                 session.add(Resource(title="Yocto Project Quick Build", type=ResourceType.DOCS, url="https://docs.yoctoproject.org/brief-yoctoprojectqs/index.html", week_id=wk.id))

    print(f"Created Phase 3.5 with 4 weeks (47-50)")

    # 5. HARDWARE UPDATE
    # -----------------------------------------------------
    print("\n--- Updating Hardware BOM ---")
    session.add(HardwareItem(name="Raspberry Pi 4 Model B (4GB)", notes="For Embedded Linux Phase", quantity=1, price_inr=5500.0, source="Robu.in", status=HardwareStatus.ORDERED))
    session.add(HardwareItem(name="SD Card (32GB Class 10)", notes="For Linux Images", quantity=2, price_inr=600.0, source="Amazon", status=HardwareStatus.ORDERED))
    
    # 6. PURGE WEB DEV (from Week 55+6 = 61? or current search by focus)
    # -----------------------------------------------------
    print("\n--- Purging Web Dev Content ---")
    # Search for week with "Interview Bootcamp Part 2" (System Design & Career)
    # Original Week 56. Shifted by +6 = 62.
    # Original Week 55 (Technical) = 61. 
    # The audit found HTML/CSS in Week 55 (Portfolio). Wait, my previous addition:
    # "Week 56 – System Design & Career" -> Tasks included "System Design", "Salary".
    # Where was HTML/CSS? Maybe implied in "Portfolio"?
    # Let's search for any Task/Day with "HTML" or "CSS"
    
    bad_items = session.exec(select(Task).where(col(Task.title).contains("HTML") | col(Task.description).contains("HTML"))).all()
    for item in bad_items:
        item.title = "Build GitHub Portfolio README"
        item.description = "Create a professional profile using Markdown"
        item.ai_prompt = "Guide me to create a stellar GitHub README for embedded engineer"
        session.add(item)
    
    print(f"Purged {len(bad_items)} HTML/CSS references.")

    session.commit()
    print("\n=== SUCCESS: Deep Audit Implemented ===")

