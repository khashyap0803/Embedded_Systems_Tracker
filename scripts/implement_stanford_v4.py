#!/usr/bin/env python3
"""
Implement Stanford Audit V4 Fixes:
1. Fix 14 broken URLs
2. Add ARM Assembly mini-module (2-3 days)
3. Add SystemVerilog basics for HW/SW co-design
4. Add Rust for Embedded as optional advanced track
"""

from datetime import date, timedelta
from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import (
    Phase, Week, DayPlan, Task, Resource, 
    ResourceType, TaskStatus
)
from sqlmodel import select, col

init_db()

print("=" * 70)
print("🎓 IMPLEMENTING STANFORD V4 AUDIT FIXES")
print("=" * 70)

with session_scope() as session:
    
    # =========================================================================
    # FIX 1: Replace 14 Broken URLs
    # =========================================================================
    print("\n--- FIX 1: Replacing Broken URLs ---")
    
    broken_urls = [
        # (search_term, new_url, new_title if needed)
        ("NXP I2C", "https://www.nxp.com/docs/en/user-guide/UM10204.pdf", None),
        ("Barr Group", "https://www.amazon.in/Embedded-Coding-Standard-Michael-Barr/dp/1442164824", "Embedded C Coding Standard (Barr Group - Amazon)"),
        ("ST Reference Manual", "https://www.st.com/resource/en/reference_manual/rm0385-stm32f75xxx-and-stm32f74xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf", "STM32F7 Reference Manual (RM0385)"),
        ("UM10204", "https://www.nxp.com/docs/en/user-guide/UM10204.pdf", None),
        ("TinyML Cookbook", "https://docs.edgeimpulse.com/docs/", "Edge Impulse Documentation"),
        ("Engineering Portfolio", "https://www.freecodecamp.org/news/how-to-build-an-impressive-github-profile/", "How to Build an Impressive GitHub Profile"),
        ("AllAboutCircuits", "https://www.allaboutcircuits.com/textbook/", "AllAboutCircuits Textbook"),
        ("LDD3", "https://lwn.net/Kernel/LDD3/", None),
        ("Device Tree for Dummies", "https://elinux.org/Device_Tree_Usage", "Device Tree Usage Guide (eLinux)"),
        ("barrgroup.com", "https://www.amazon.in/Embedded-Coding-Standard-Michael-Barr/dp/1442164824", "Embedded C Coding Standard (Amazon)"),
    ]
    
    fixed_count = 0
    for search_term, new_url, new_title in broken_urls:
        resources = session.exec(select(Resource).where(Resource.title.contains(search_term))).all()
        for r in resources:
            r.url = new_url
            if new_title:
                r.title = new_title
            session.add(r)
            fixed_count += 1
    session.commit()
    print(f"✅ Fixed {fixed_count} URL references")
    
    # =========================================================================
    # FIX 2: Add ARM Assembly Mini-Module (2-3 days)
    # =========================================================================
    print("\n--- FIX 2: Adding ARM Assembly Mini-Module ---")
    
    # Find a suitable week in Phase 1 (maybe Week 6 or after C programming)
    phase1 = session.exec(select(Phase).where(Phase.name.contains("Phase 1"))).first()
    
    # Check if ARM Assembly week already exists
    existing_asm = session.exec(select(Week).where(Week.focus.contains("ARM Assembly"))).first()
    
    if existing_asm:
        print("ARM Assembly week already exists, skipping...")
    else:
        # Insert at Week 7 (shift others if needed)
        target_week = 7
        
        # Check if Week 7 exists and shift if needed
        existing_w7 = session.exec(select(Week).where(Week.number == target_week)).first()
        if existing_w7 and "Assembly" not in existing_w7.focus:
            # Shift weeks >= 7 by +1
            weeks_to_shift = session.exec(select(Week).where(Week.number >= target_week).order_by(col(Week.number).desc())).all()
            for w in weeks_to_shift:
                w.number += 1
                session.add(w)
            session.commit()
            print(f"Shifted {len(weeks_to_shift)} weeks to make room")
        
        # Create ARM Assembly week
        asm_week = Week(
            number=target_week,
            phase_id=phase1.id,
            focus="Week 07 – ARM Assembly Fundamentals for Debugging",
            start_date=date(2025, 2, 15),
        )
        session.add(asm_week)
        session.commit()
        session.refresh(asm_week)
        
        # Add days
        asm_days = [
            "ARM Instruction Set Architecture (ISA) Overview",
            "ARM Registers (R0-R15, CPSR, SPSR)",
            "ARM Assembly Syntax and Common Instructions",
            "Inline Assembly in C for Performance",
            "Reading Disassembly for Debugging",
            "ARM Thumb Mode and Code Density",
            "Project: Optimize a Hot Loop in Assembly",
        ]
        for i, focus in enumerate(asm_days, 1):
            session.add(DayPlan(number=i, focus=focus, week_id=asm_week.id))
        
        # Add resources
        asm_resources = [
            ("ARM Assembly Tutorial", ResourceType.ARTICLE, "https://azeria-labs.com/writing-arm-assembly-part-1/"),
            ("ARM Assembly Cheatsheet", ResourceType.DOCS, "https://developer.arm.com/documentation/dui0489/latest/arm-and-thumb-instructions/instruction-summary"),
            ("ARM Cortex-M Programmer's Model", ResourceType.DOCS, "https://developer.arm.com/documentation/dui0553/latest/"),
        ]
        for title, rtype, url in asm_resources:
            session.add(Resource(title=title, type=rtype, url=url, week_id=asm_week.id))
        
        session.commit()
        print(f"✅ Created ARM Assembly Week {target_week}")
    
    # =========================================================================
    # FIX 3: Add SystemVerilog Basics (for HW/SW co-design roles)
    # =========================================================================
    print("\n--- FIX 3: Adding SystemVerilog Basics ---")
    
    existing_sv = session.exec(select(Week).where(Week.focus.contains("SystemVerilog"))).first()
    
    if existing_sv:
        print("SystemVerilog week already exists, skipping...")
    else:
        # Add as optional advanced content after Phase 3
        phase3 = session.exec(select(Phase).where(Phase.name.contains("Phase 3") & ~Phase.name.contains("3.5"))).first()
        
        # Find next available week number after week 40
        max_week = session.exec(select(Week).order_by(col(Week.number).desc())).first()
        sv_week_num = max_week.number + 1 if max_week else 70
        
        sv_week = Week(
            number=sv_week_num,
            phase_id=phase3.id if phase3 else 3,
            focus=f"Week {sv_week_num} – SystemVerilog Basics for HW/SW Co-Design (Optional)",
            start_date=date(2025, 12, 1),
        )
        session.add(sv_week)
        session.commit()
        session.refresh(sv_week)
        
        sv_days = [
            "Digital Logic Refresher (Gates, Flip-Flops)",
            "Verilog Basics: Modules and Ports",
            "SystemVerilog: Always Blocks and FSMs",
            "Testbench Writing for Verification",
            "Reading RTL to Understand HW Behavior",
            "AXI/AHB Bus Protocols Overview",
            "Project: Simulate SPI Controller in Verilator",
        ]
        for i, focus in enumerate(sv_days, 1):
            session.add(DayPlan(number=i, focus=focus, week_id=sv_week.id))
        
        sv_resources = [
            ("HDLBits - Interactive Verilog", ResourceType.COURSE, "https://hdlbits.01xz.net/wiki/Main_Page"),
            ("SystemVerilog Tutorial", ResourceType.ARTICLE, "https://www.chipverify.com/systemverilog/systemverilog-tutorial"),
            ("Verilator Intro", ResourceType.TOOL, "https://verilator.org/guide/latest/"),
        ]
        for title, rtype, url in sv_resources:
            session.add(Resource(title=title, type=rtype, url=url, week_id=sv_week.id))
        
        session.commit()
        print(f"✅ Created SystemVerilog Week {sv_week_num}")
    
    # =========================================================================
    # FIX 4: Add Rust for Embedded (Optional Advanced Track)
    # =========================================================================
    print("\n--- FIX 4: Adding Rust for Embedded Track ---")
    
    existing_rust = session.exec(select(Week).where(Week.focus.contains("Rust"))).first()
    
    if existing_rust:
        print("Rust week already exists, skipping...")
    else:
        phase4 = session.exec(select(Phase).where(Phase.name.contains("Phase 4"))).first()
        
        max_week = session.exec(select(Week).order_by(col(Week.number).desc())).first()
        rust_week_num = max_week.number + 1 if max_week else 71
        
        rust_week = Week(
            number=rust_week_num,
            phase_id=phase4.id if phase4 else 4,
            focus=f"Week {rust_week_num} – Rust for Embedded Systems (Optional Advanced)",
            start_date=date(2025, 12, 8),
        )
        session.add(rust_week)
        session.commit()
        session.refresh(rust_week)
        
        rust_days = [
            "Rust Ownership and Borrowing Basics",
            "no_std Rust for Bare-Metal",
            "embedded-hal and PAC Crates",
            "Rust on STM32 with probe-rs",
            "Error Handling with Result<> in Embedded",
            "Memory Safety Benefits for Embedded",
            "Project: Blink LED + UART in Rust",
        ]
        for i, focus in enumerate(rust_days, 1):
            session.add(DayPlan(number=i, focus=focus, week_id=rust_week.id))
        
        rust_resources = [
            ("The Embedded Rust Book", ResourceType.BOOK, "https://docs.rust-embedded.org/book/"),
            ("Discovery Book (STM32)", ResourceType.BOOK, "https://docs.rust-embedded.org/discovery/"),
            ("probe-rs Debugger", ResourceType.TOOL, "https://probe.rs/"),
            ("embassy Async Framework", ResourceType.REPO, "https://embassy.dev/"),
        ]
        for title, rtype, url in rust_resources:
            session.add(Resource(title=title, type=rtype, url=url, week_id=rust_week.id))
        
        session.commit()
        print(f"✅ Created Rust for Embedded Week {rust_week_num}")

print("\n" + "=" * 70)
print("✅ ALL STANFORD V4 FIXES IMPLEMENTED!")
print("=" * 70)
