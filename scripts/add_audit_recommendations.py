#!/usr/bin/env python3
"""Add audit report recommendations to the database."""

from datetime import date
from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import (
    Phase, Week, DayPlan, Task, Resource, HardwareItem, 
    ResourceType, TaskStatus, HardwareStatus
)
from sqlmodel import select

init_db()

# ============================================================================
# PART 1: Add Week 0 Pre-Requisite Ramp-Up
# ============================================================================
print("=" * 60)
print("PART 1: Adding Week 0 Pre-Requisite Ramp-Up")
print("=" * 60)

with session_scope() as session:
    phase1 = session.exec(select(Phase).where(Phase.name.contains("Phase 1"))).first()
    if not phase1:
        print("ERROR: Phase 1 not found!")
        exit(1)
    
    # Check if Week 0 already exists
    existing = session.exec(select(Week).where(Week.number == 0)).first()
    if existing:
        print("Week 0 already exists, skipping...")
    else:
        week0 = Week(
            number=0, phase_id=phase1.id,
            focus="Week 00 – Pre-Requisite Bootcamp (Complete Beginner Ramp-Up)",
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 7),
        )
        session.add(week0)
        session.commit()
        session.refresh(week0)
        
        # Days
        for i in range(1, 8):
            focuses = [
                "C Programming – Variables, loops, functions",
                "C Programming – Pointers and memory",
                "Electronics 101 – Voltage, current, Ohm's law",
                "Electronics 101 – Components (resistors, capacitors, LEDs)",
                "Linux Terminal – Navigation, file operations",
                "Linux Terminal – GCC compilation, Makefiles",
                "Number Systems – Binary, hexadecimal, 2's complement",
            ]
            day = DayPlan(number=i, week_id=week0.id, focus=focuses[i-1], 
                     scheduled_date=date(2025, 1, i))
            session.add(day)
        session.commit()
        
        # Get days
        days = session.exec(select(DayPlan).where(DayPlan.week_id == week0.id)).all()
        
        # Tasks (3 per day = 21 total)
        tasks_data = [
            (1, 1, "Install GCC and VS Code", "Set up C dev environment", "Guide me through GCC and VS Code setup for C"),
            (1, 2, "Write Hello World program", "First C program", "Explain C compilation process step by step"),
            (1, 3, "Variables and data types practice", "int, char, float", "Create C data types exercises"),
            (2, 1, "Pointer fundamentals", "Address-of and dereference", "Explain C pointers with memory diagrams"),
            (2, 2, "Pointer arithmetic", "Array traversal", "Create pointer exercises for embedded"),
            (2, 3, "Functions with pointers", "Pass by reference", "Show register access using pointers"),
            (3, 1, "Voltage, current, resistance", "Basic concepts", "Explain V/I/R with water analogy"),
            (3, 2, "Ohm's Law calculations", "V = IR problems", "Generate 10 Ohm's law problems"),
            (3, 3, "Series and parallel circuits", "Equivalent resistance", "Explain circuit combinations"),
            (4, 1, "Resistor color codes", "Reading values", "Create resistor color code quiz"),
            (4, 2, "Capacitors and LEDs", "Basic usage", "Explain capacitors and LED polarity"),
            (4, 3, "Build LED circuit", "Hands-on breadboard", "Guide LED circuit with resistor calculation"),
            (5, 1, "Terminal navigation", "cd, ls, pwd, mkdir", "Create Linux terminal exercise"),
            (5, 2, "File viewing commands", "cat, grep, head, tail", "Show grep for embedded debugging"),
            (5, 3, "Text editors intro", "nano and vim basics", "Teach essential vim commands"),
            (6, 1, "GCC compilation flags", "-o, -c, -g, -Wall", "Explain GCC flags for embedded"),
            (6, 2, "Multi-file compilation", "Separate compilation", "Show multi-file project compilation"),
            (6, 3, "Makefile basics", "Targets, dependencies", "Create simple embedded Makefile"),
            (7, 1, "Binary number system", "Conversion and counting", "Explain binary for registers"),
            (7, 2, "Hexadecimal numbers", "Memory addresses", "Show why hex for memory"),
            (7, 3, "2's complement", "Signed integers", "Explain negative number representation"),
        ]
        
        for day_num, hour, title, desc, prompt in tasks_data:
            day = next((d for d in days if d.number == day_num), None)
            if day:
                task = Task(title=title, description=desc, ai_prompt=prompt,
                           day_id=day.id, hour_number=hour, estimated_hours=1.0)
                session.add(task)
        session.commit()
        
        # Resources
        resources = [
            ("CS50 C Programming (Harvard)", ResourceType.VIDEO, "https://cs50.harvard.edu/x/2024/weeks/1/"),
            ("Learn C - Programiz", ResourceType.ARTICLE, "https://www.programiz.com/c-programming"),
            ("SparkFun Electronics Tutorial", ResourceType.ARTICLE, "https://learn.sparkfun.com/tutorials/voltage-current-resistance-and-ohms-law"),
            ("Linux Journey - Command Line", ResourceType.ARTICLE, "https://linuxjourney.com/lesson/the-shell"),
            ("Hex and Binary for Embedded", ResourceType.VIDEO, "https://www.youtube.com/watch?v=rsxT4FfRBaM"),
        ]
        for title, rtype, url in resources:
            session.add(Resource(title=title, type=rtype, url=url, week_id=week0.id))
        session.commit()
        print("✅ Week 0 created with 7 days, 21 tasks, 5 resources")

# ============================================================================
# PART 2: Add Interview Prep Block (Week 55-56)
# ============================================================================
print("\n" + "=" * 60)
print("PART 2: Adding Interview Prep Block")
print("=" * 60)

with session_scope() as session:
    phase4 = session.exec(select(Phase).where(Phase.name.contains("Phase 4"))).first()
    if not phase4:
        print("ERROR: Phase 4 not found!")
    else:
        # Check for existing
        existing55 = session.exec(select(Week).where(Week.number == 55)).first()
        if existing55:
            print("Week 55 already exists, skipping...")
        else:
            # Week 55 - Interview Prep
            week55 = Week(
                number=55, phase_id=phase4.id,
                focus="Week 55 – Interview Bootcamp Part 1 (Technical Questions)",
                start_date=date(2025, 12, 15), end_date=date(2025, 12, 21),
            )
            session.add(week55)
            session.commit()
            session.refresh(week55)
            
            # Days and tasks for Week 55
            interview_topics = [
                ("Volatile, static, const keywords", "Core C interview questions"),
                ("Interrupt handling and ISR safety", "Critical embedded concepts"),
                ("Memory management in embedded", "Stack, heap, static allocation"),
                ("Pointer and bit manipulation problems", "Common coding questions"),
                ("RTOS concepts - tasks, semaphores, mutexes", "Real-time interview topics"),
                ("Communication protocols deep dive", "I2C, SPI, UART, CAN questions"),
                ("Mock interview practice day", "Full interview simulation"),
            ]
            
            for i, (focus, desc) in enumerate(interview_topics, 1):
                day = DayPlan(number=i, week_id=week55.id, focus=focus,
                         scheduled_date=date(2025, 12, 14+i))
                session.add(day)
            session.commit()
            
            days = session.exec(select(DayPlan).where(DayPlan.week_id == week55.id)).all()
            
            interview_tasks = [
                (1, "Master volatile keyword usage", "Explain volatile with compiler optimization examples"),
                (1, "Static keyword in embedded C", "Show static for memory persistence and scope"),
                (2, "ISR design best practices", "Create checklist for interrupt-safe code"),
                (2, "Reentrant functions", "Explain reentrancy and thread safety"),
                (3, "Memory map analysis", "Show how to read a linker map file"),
                (3, "Stack overflow detection", "Explain stack canaries and monitoring"),
                (4, "Bit manipulation exercises", "Generate 10 bit twiddling problems"),
                (4, "Pointer puzzles", "Create tricky pointer interview questions"),
                (5, "RTOS priority inversion explanation", "Explain with Mars Pathfinder example"),
                (5, "Deadlock prevention strategies", "Show resource ordering technique"),
                (6, "Protocol timing analysis", "Calculate I2C/SPI speeds from datasheets"),
                (6, "CAN message arbitration", "Explain priority and message IDs"),
                (7, "Full mock interview", "Conduct 45-minute embedded interview"),
                (7, "Interview retrospective", "Analyze performance and gaps"),
            ]
            
            for day_num, title, prompt in interview_tasks:
                day = next((d for d in days if d.number == day_num), None)
                if day:
                    session.add(Task(title=title, ai_prompt=prompt, day_id=day.id,
                                    hour_number=(1 if interview_tasks.index((day_num, title, prompt)) % 2 == 0 else 2)))
            session.commit()
            
            # Week 55 resources
            w55_resources = [
                ("Embedded Systems Interview Questions", ResourceType.ARTICLE, "https://github.com/search?q=embedded+interview+questions"),
                ("Volatile Keyword Explained", ResourceType.ARTICLE, "https://interrupt.memfault.com/blog/arm-cortex-m-exceptions-and-nvic"),
                ("Interviewing.io Practice", ResourceType.ARTICLE, "https://interviewing.io/"),
            ]
            for title, rtype, url in w55_resources:
                session.add(Resource(title=title, type=rtype, url=url, week_id=week55.id))
            session.commit()
            print("✅ Week 55 Interview Prep created")
            
        # Week 56 - System Design
        existing56 = session.exec(select(Week).where(Week.number == 56)).first()
        if existing56:
            print("Week 56 already exists, skipping...")
        else:
            week56 = Week(
                number=56, phase_id=phase4.id,
                focus="Week 56 – Interview Bootcamp Part 2 (System Design & Career)",
                start_date=date(2025, 12, 22), end_date=date(2025, 12, 28),
            )
            session.add(week56)
            session.commit()
            session.refresh(week56)
            
            sysdesign_days = [
                "System Design - Smart thermostat",
                "System Design - GPS tracker",
                "System Design - Industrial sensor network",
                "Take-home coding challenge practice",
                "Behavioral interview (STAR method)",
                "Salary negotiation strategies",
                "Final prep and confidence building",
            ]
            
            for i, focus in enumerate(sysdesign_days, 1):
                session.add(DayPlan(number=i, week_id=week56.id, focus=focus,
                               scheduled_date=date(2025, 12, 21+i)))
            session.commit()
            print("✅ Week 56 System Design & Career created")

# ============================================================================
# PART 3: Add Hardware BOM Items
# ============================================================================
print("\n" + "=" * 60)
print("PART 3: Adding Hardware BOM Items")
print("=" * 60)

with session_scope() as session:
    hardware_items = [
        ("Rigol DS1054Z Oscilloscope", "Essential for debugging analog signals", 25000, "Amazon.in"),
        ("Hantek 6022BE USB Oscilloscope", "Budget alternative to Rigol", 8000, "Amazon.in"),
        ("TJA1050 CAN Transceiver Module", "For CAN bus projects (Week 19)", 150, "Robu.in"),
        ("MCP2551 CAN Transceiver", "Alternative CAN transceiver", 180, "Robu.in"),
        ("TJA1020 LIN Transceiver", "For LIN bus projects", 200, "Robu.in"),
        ("CAN Bus Development Kit", "Complete CAN learning kit", 1500, "Robu.in"),
    ]
    
    for name, notes, price, source in hardware_items:
        existing = session.exec(select(HardwareItem).where(HardwareItem.name == name)).first()
        if existing:
            print(f"  {name} already exists, skipping...")
        else:
            item = HardwareItem(
                name=name, notes=notes, quantity=1,
                price_inr=float(price), source=source,
                status=HardwareStatus.ORDERED
            )
            session.add(item)
            print(f"  ✅ Added: {name} (₹{price})")
    session.commit()

# ============================================================================
# PART 4: Add AUTOSAR Week
# ============================================================================
print("\n" + "=" * 60)
print("PART 4: Adding AUTOSAR Introduction Week")
print("=" * 60)

with session_scope() as session:
    phase3 = session.exec(select(Phase).where(Phase.name.contains("Phase 3"))).first()
    if not phase3:
        print("ERROR: Phase 3 not found!")
    else:
        existing = session.exec(select(Week).where(Week.focus.contains("AUTOSAR"))).first()
        if existing:
            print("AUTOSAR week already exists, skipping...")
        else:
            autosar_week = Week(
                number=44, phase_id=phase3.id,
                focus="Week 44 – AUTOSAR Fundamentals for Automotive Embedded",
                start_date=date(2025, 10, 1), end_date=date(2025, 10, 7),
            )
            session.add(autosar_week)
            session.commit()
            session.refresh(autosar_week)
            
            autosar_days = [
                "AUTOSAR architecture overview",
                "Basic Software (BSW) layers",
                "Application Software Components (SWC)",
                "Runtime Environment (RTE)",
                "AUTOSAR Configurator tools",
                "Classic vs Adaptive AUTOSAR",
                "AUTOSAR hands-on with EB Tresos demo",
            ]
            
            for i, focus in enumerate(autosar_days, 1):
                session.add(DayPlan(number=i, week_id=autosar_week.id, focus=focus,
                               scheduled_date=date(2025, 10, i)))
            session.commit()
            
            autosar_resources = [
                ("AUTOSAR Official Documentation", ResourceType.DOCS, "https://www.autosar.org/standards"),
                ("AUTOSAR Tutorial - Vector", ResourceType.VIDEO, "https://www.vector.com/int/en/know-how/autosar/"),
                ("EB Tresos Studio (Free Eval)", ResourceType.TOOL, "https://www.elektrobit.com/products/ecu/eb-tresos/studio/"),
            ]
            for title, rtype, url in autosar_resources:
                session.add(Resource(title=title, type=rtype, url=url, week_id=autosar_week.id))
            session.commit()
            print("✅ AUTOSAR Week 44 created")

# ============================================================================
# PART 5: Add DSP Prerequisites before TinyML
# ============================================================================
print("\n" + "=" * 60)
print("PART 5: Adding DSP Prerequisites Resources")
print("=" * 60)

with session_scope() as session:
    # Find TinyML week (Week 39)
    tinyml_week = session.exec(select(Week).where(Week.number == 39)).first()
    if tinyml_week:
        dsp_resources = [
            ("DSP Fundamentals for Embedded", ResourceType.VIDEO, "https://www.youtube.com/playlist?list=PLUMWjy5jgHK1NC52DXXrriwihVrYZKqjk"),
            ("FFT Explained Simply", ResourceType.ARTICLE, "https://www.dspguide.com/ch12.htm"),
            ("Digital Filters Primer", ResourceType.ARTICLE, "https://www.analog.com/en/design-center/landing-pages/001/beginners-guide-to-dsp.html"),
        ]
        for title, rtype, url in dsp_resources:
            existing = session.exec(select(Resource).where(Resource.title == title)).first()
            if not existing:
                session.add(Resource(title=title, type=rtype, url=url, week_id=tinyml_week.id))
                print(f"  ✅ Added DSP resource: {title}")
        session.commit()
    else:
        print("Week 39 not found, skipping DSP resources")

print("\n" + "=" * 60)
print("✅ ALL AUDIT RECOMMENDATIONS IMPLEMENTED!")
print("=" * 60)
