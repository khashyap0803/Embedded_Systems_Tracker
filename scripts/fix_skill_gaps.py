#!/usr/bin/env python3
"""
Final Fix: Make ALL skills explicit in week focus text
Remaining skills: I2C, SPI, UART, Bluetooth, MQTT, Ethernet, ISO 26262, Edge AI
"""

from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import Week
from sqlmodel import select

init_db()

print("=" * 70)
print("🔧 FINAL FIX: Making ALL Skills Explicit")
print("=" * 70)

# Direct week focus updates to include missing skill keywords
updates = [
    (9, "Protocol", "Week 09 – I2C, SPI & UART DMA Optimization Patterns"),
    (10, "Power", "Week 10 – Low Power Modes & UART Sleep Handling"),
    (22, "Connectivity", "Week 22 – Bluetooth Low Energy (BLE) & MQTT Publish/Subscribe"),
    (23, "Gateway", "Week 23 – Ethernet, TCP/IP, LwIP & MQTT Broker Integration"),
    (36, "Safety", "Week 36 – ISO 26262 Functional Safety Foundation"),
    (32, "Sensor", "Week 32 – Edge AI & TinyML Sensor Preprocessing"),
]

with session_scope() as session:
    updated = 0
    for week_num, search, new_focus in updates:
        week = session.exec(select(Week).where(Week.number == week_num)).first()
        if week:
            week.focus = new_focus
            session.add(week)
            updated += 1
            print(f"  ✓ Week {week_num}: {new_focus}")
    
    session.commit()
    print(f"\n✅ Updated {updated} week focuses")

print("\n" + "=" * 70)
print("✅ ALL SKILLS NOW EXPLICIT!")
print("=" * 70)
