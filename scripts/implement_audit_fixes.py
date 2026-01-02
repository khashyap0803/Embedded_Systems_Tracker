#!/usr/bin/env python3
"""
Curriculum Audit Fixes Implementation Script
Implements:
1. Insert new Week 8 (Timers, PWM & Waveform Generation) with 7 days × 3 tasks
2. Renumber all subsequent weeks (+1)
3. Replace generic tasks with ADC-focused tasks
4. Rename U-Boot to MCUBoot for Cortex-M weeks
5. Update project dates (+7 days)

Final: 72 weeks, 504 days, 1512 tasks
"""

import sqlite3
from datetime import date, timedelta

DB_PATH = '/home/nani/.local/share/embedded-tracker/embedded_tracker.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("CURRICULUM AUDIT FIXES IMPLEMENTATION")
    print("=" * 60)
    
    # Get Phase 1 ID
    cursor.execute("SELECT id FROM phase WHERE name LIKE '%Phase 1%' LIMIT 1")
    phase1_id = cursor.fetchone()[0]
    print(f"\nPhase 1 ID: {phase1_id}")
    
    # Get current Week 7 and Week 8 info for date calculation
    cursor.execute("SELECT id, end_date FROM week WHERE number = 7")
    week7 = cursor.fetchone()
    week7_id, week7_end = week7[0], week7[1]
    
    cursor.execute("SELECT id, start_date FROM week WHERE number = 8")
    week8 = cursor.fetchone()
    old_week8_id, week8_start = week8[0], week8[1]
    
    print(f"Week 7 ID: {week7_id}, ends: {week7_end}")
    print(f"Current Week 8 ID: {old_week8_id}, starts: {week8_start}")
    
    # =========================================================================
    # STEP 1: Shift all weeks >= 8 by +1
    # =========================================================================
    print("\n[1/6] Shifting week numbers >= 8 by +1...")
    
    # Get all weeks >= 8 in descending order to avoid conflicts
    cursor.execute("SELECT id, number FROM week WHERE number >= 8 ORDER BY number DESC")
    weeks_to_shift = cursor.fetchall()
    
    for week_id, week_num in weeks_to_shift:
        new_num = week_num + 1
        # Update week number in focus title too
        cursor.execute("SELECT focus FROM week WHERE id = ?", (week_id,))
        focus = cursor.fetchone()[0]
        if focus and f"Week {week_num:02d}" in focus:
            new_focus = focus.replace(f"Week {week_num:02d}", f"Week {new_num:02d}")
            cursor.execute("UPDATE week SET number = ?, focus = ? WHERE id = ?", 
                         (new_num, new_focus, week_id))
        else:
            cursor.execute("UPDATE week SET number = ? WHERE id = ?", (new_num, week_id))
    
    print(f"  Shifted {len(weeks_to_shift)} weeks")
    
    # =========================================================================
    # STEP 2: Insert new Week 8 (Timers, PWM & Waveform Generation)
    # =========================================================================
    print("\n[2/6] Creating new Week 8 (Timers, PWM & Waveform Generation)...")
    
    # Calculate dates
    new_week_start = date.fromisoformat(week7_end) + timedelta(days=1)
    new_week_end = new_week_start + timedelta(days=6)
    
    cursor.execute("""
        INSERT INTO week (number, focus, phase_id, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        8,
        "Week 08 – Timers, PWM & Waveform Generation",
        phase1_id,
        new_week_start.isoformat(),
        new_week_end.isoformat(),
        "pending"
    ))
    new_week8_id = cursor.lastrowid
    print(f"  Created new Week 8 (ID: {new_week8_id})")
    
    # =========================================================================
    # STEP 3: Create 7 days for new Week 8
    # =========================================================================
    print("\n[3/6] Creating 7 days for new Week 8...")
    
    day_focuses = [
        "TIMx Peripheral Architecture & Clock Configuration",
        "Timer Interrupt Modes (Update, Compare, Capture)",
        "Hardware PWM Generation & LED Dimming",
        "Input Capture for Signal Measurement",
        "Output Compare & Precise Pulse Generation",
        "Integration: Servo & Motor Control",
        "Timer Review & Practice"
    ]
    
    day_ids = []
    for i, focus in enumerate(day_focuses, 1):
        day_date = new_week_start + timedelta(days=i-1)
        cursor.execute("""
            INSERT INTO dayplan (number, focus, week_id, scheduled_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (i, focus, new_week8_id, day_date.isoformat(), "pending"))
        day_ids.append(cursor.lastrowid)
    
    print(f"  Created {len(day_ids)} days")
    
    # =========================================================================
    # STEP 4: Create 21 tasks (3 per day) for new Week 8
    # =========================================================================
    print("\n[4/6] Creating 21 tasks for new Week 8...")
    
    tasks_by_day = [
        # Day 1: TIMx Architecture
        [
            ("Understand STM32 TIMx peripheral clock tree and prescaler configuration", 
             "Explain TIM clock sources and APB bus connections"),
            ("Configure basic timer with HAL_TIM_Base_Start and counter modes",
             "Set up TIM2 for periodic 1Hz tick generation"),
            ("Implement timer update interrupt callback for LED toggle",
             "Create interrupt-driven blinking without main loop polling")
        ],
        # Day 2: Timer Interrupts
        [
            ("Configure timer update interrupt with HAL_TIM_Base_Start_IT",
             "Setup TIM3 update interrupt at 10ms period"),
            ("Implement periodic callback for sensor polling",
             "Create timed sampling routine using timer interrupt"),
            ("Design timeout handler using one-pulse mode",
             "Build communication timeout detector with TIM OPM")
        ],
        # Day 3: Hardware PWM
        [
            ("Configure PWM output using HAL_TIM_PWM_Start on TIM channel",
             "Initialize TIM1 CH1 for PWM generation"),
            ("Implement duty cycle control for LED brightness",
             "Create smooth LED fade effect using PWM duty variation"),
            ("Generate multi-channel PWM for RGB LED control",
             "Drive RGB LED with synchronized PWM channels")
        ],
        # Day 4: Input Capture
        [
            ("Configure input capture mode for rising edge detection",
             "Setup TIM2 IC for external signal capture"),
            ("Measure pulse width using input capture timestamps",
             "Calculate signal duty cycle from capture values"),
            ("Build frequency meter using input capture period",
             "Create real-time frequency display for input signal")
        ],
        # Day 5: Output Compare
        [
            ("Configure output compare mode for precise timing",
             "Setup TIM3 OC for microsecond-accurate pulses"),
            ("Generate encoder simulation pulses with output compare",
             "Create quadrature encoder test signals"),
            ("Implement IR protocol timing with output compare",
             "Generate NEC-compatible IR carrier modulation")
        ],
        # Day 6: Integration
        [
            ("Control servo motor position with PWM pulse width",
             "Drive SG90 servo through 0-180 degree range"),
            ("Implement DC motor speed control with PWM duty cycle",
             "Control motor speed using L298N driver with PWM"),
            ("Build buzzer tone generator with timer frequency control",
             "Create musical tones using timer-driven piezo buzzer")
        ],
        # Day 7: Review
        [
            ("Review STM32 timer architecture and modes",
             "Consolidate TIMx peripheral configuration patterns"),
            ("Practice timer configuration exercises",
             "Complete timer setup challenges without reference"),
            ("Prepare for DMA by understanding timer-DMA interactions",
             "Study DMA trigger mechanisms from timer events")
        ]
    ]
    
    from datetime import datetime
    NOW = datetime.utcnow().isoformat()
    
    task_count = 0
    for day_idx, day_tasks in enumerate(tasks_by_day):
        day_id = day_ids[day_idx]
        for hour, (title, ai_prompt) in enumerate(day_tasks, 1):
            cursor.execute("""
                INSERT INTO task (title, ai_prompt, week_id, day_id, hour_number, status,
                                  status_updated_at, total_work_seconds, total_break_seconds, total_pause_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
            """, (title, ai_prompt, new_week8_id, day_id, hour, "pending", NOW))
            task_count += 1
    
    print(f"  Created {task_count} tasks")
    
    # =========================================================================
    # STEP 5: Add ADC tasks (replace generic in Week 10 - now Week 11)
    # =========================================================================
    print("\n[5/6] Adding ADC-focused tasks...")
    
    # Find Week 10 (now Week 11 after shift) - I2C/SPI/UART week
    cursor.execute("SELECT id FROM week WHERE number = 11")
    week11_id = cursor.fetchone()[0]
    
    # Find generic tasks to replace
    generic_patterns = ['integration planning', 'integration testing', 'integration review',
                       'deep dive study', 'hands-on practice']
    
    adc_tasks = [
        ("Configure ADC for continuous multi-channel scanning mode", 
         "Setup ADC1 scan sequence with multiple channels"),
        ("Implement DMA-driven ADC with circular buffer",
         "Create non-blocking ADC sampling using DMA transfer"),
        ("Build analog signal conditioning with software oversampling",
         "Implement 16x oversampling for enhanced ADC resolution"),
        ("Design ADC calibration routine for offset compensation",
         "Create factory calibration storage and runtime application"),
        ("Configure analog watchdog for threshold monitoring",
         "Setup AWD interrupt for out-of-range detection")
    ]
    
    adc_count = 0
    for title, ai_prompt in adc_tasks:
        # Find a generic task to replace
        cursor.execute("""
            SELECT t.id FROM task t 
            WHERE t.week_id = ? AND (
                LOWER(t.title) LIKE '%integration planning%' OR
                LOWER(t.title) LIKE '%integration testing%' OR
                LOWER(t.title) LIKE '%integration review%' OR
                LOWER(t.title) LIKE '%deep dive%' OR
                LOWER(t.title) LIKE '%hands-on practice%' OR
                LOWER(t.title) LIKE '%knowledge application%'
            )
            LIMIT 1
        """, (week11_id,))
        result = cursor.fetchone()
        if result:
            task_id = result[0]
            cursor.execute("UPDATE task SET title = ?, ai_prompt = ? WHERE id = ?",
                         (title, ai_prompt, task_id))
            adc_count += 1
    
    print(f"  Replaced {adc_count} generic tasks with ADC-focused content")
    
    # =========================================================================
    # STEP 6: Rename U-Boot to MCUBoot (Week 12 -> now Week 13)
    # =========================================================================
    print("\n[6/6] Renaming U-Boot to MCUBoot...")
    
    cursor.execute("""
        UPDATE task SET 
            title = 'Configure MCUBoot secure bootloader for STM32 Cortex-M',
            ai_prompt = 'Setup MCUBoot with image signing and verification'
        WHERE LOWER(title) LIKE '%u-boot%' AND LOWER(title) LIKE '%cortex-m%'
    """)
    
    cursor.execute("""
        UPDATE task SET 
            title = 'Build MCUBoot with signed image verification',
            ai_prompt = 'Configure MCUBoot for secure boot with RSA/ECDSA signatures'
        WHERE LOWER(title) LIKE '%u-boot%' AND LOWER(title) LIKE '%device tree%'
    """)
    
    print(f"  Updated U-Boot references to MCUBoot")
    
    # =========================================================================
    # STEP 7: Shift project dates by +7 days (for phases 2+)
    # =========================================================================
    print("\n[7/6] Updating project dates (+7 days)...")
    
    cursor.execute("""
        UPDATE project SET 
            due_date = date(due_date, '+7 days'),
            start_date = CASE WHEN start_date IS NOT NULL THEN date(start_date, '+7 days') ELSE NULL END
        WHERE phase_id > ?
    """, (phase1_id,))
    
    projects_updated = cursor.rowcount
    print(f"  Updated {projects_updated} project dates")
    
    # =========================================================================
    # VERIFICATION
    # =========================================================================
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM week")
    weeks = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dayplan")
    days = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM task")
    tasks = cursor.fetchone()[0]
    
    print(f"\nFinal counts:")
    print(f"  Weeks: {weeks} (expected: 72)")
    print(f"  Days: {days} (expected: 504)")
    print(f"  Tasks: {tasks} (expected: 1512)")
    
    # Check week sequence
    cursor.execute("SELECT number FROM week ORDER BY number")
    week_nums = [r[0] for r in cursor.fetchall()]
    expected_nums = list(range(0, 72))
    if week_nums == expected_nums:
        print("  ✅ Week sequence: 0-71 correct")
    else:
        print(f"  ❌ Week sequence issue: {week_nums[:5]}...{week_nums[-5:]}")
    
    # Check new Week 8
    cursor.execute("SELECT focus FROM week WHERE number = 8")
    week8_focus = cursor.fetchone()[0]
    print(f"  New Week 8: {week8_focus[:50]}...")
    
    # Check MCUBoot rename
    cursor.execute("SELECT COUNT(*) FROM task WHERE LOWER(title) LIKE '%mcuboot%'")
    mcuboot = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM task WHERE LOWER(title) LIKE '%u-boot%'")
    uboot = cursor.fetchone()[0]
    print(f"  MCUBoot tasks: {mcuboot}, U-Boot tasks: {uboot}")
    
    # Commit changes
    conn.commit()
    print("\n✅ All changes committed successfully!")
    
    conn.close()

if __name__ == "__main__":
    main()
