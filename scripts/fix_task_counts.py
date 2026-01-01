#!/usr/bin/env python3
"""Comprehensive fix for task hierarchy - ensure 21 tasks per week (7 days x 3 tasks)."""

import sqlite3
from datetime import datetime

db_path = '/home/nani/.local/share/embedded-tracker/embedded_tracker.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

now = datetime.now().isoformat()

print("=" * 80)
print("COMPREHENSIVE TASK HIERARCHY FIX")
print("=" * 80)

# Default task template based on day number
def get_default_tasks(day_focus, day_num):
    """Generate 3 tasks based on day focus or generic topics."""
    if not day_focus:
        day_focus = f"Day {day_num} Studies"
    
    topic = day_focus.split('–')[-1].strip() if '–' in day_focus else day_focus
    topic = topic[:30]  # Truncate
    
    return [
        (f"Study {topic} fundamentals", f"Learn core concepts of {topic}"),
        (f"Practice {topic} exercises", f"Complete hands-on exercises for {topic}"),
        (f"Apply {topic} in project", f"Build mini-project demonstrating {topic}")
    ]

# Get all days
cursor.execute('''
    SELECT d.id, d.number, d.focus, d.week_id, w.number as week_num
    FROM dayplan d
    JOIN week w ON d.week_id = w.id
    ORDER BY w.number, d.number
''')
all_days = cursor.fetchall()

fixed_count = 0
for day_id, day_num, day_focus, week_id, week_num in all_days:
    # Count current tasks for this day
    cursor.execute('SELECT COUNT(*) FROM task WHERE day_id = ?', (day_id,))
    task_count = cursor.fetchone()[0]
    
    if task_count == 3:
        continue  # Already correct
    
    if task_count > 3:
        # Delete extras (keep first 3)
        cursor.execute('''
            DELETE FROM task WHERE id IN (
                SELECT id FROM task WHERE day_id = ? 
                ORDER BY hour_number LIMIT -1 OFFSET 3
            )
        ''', (day_id,))
        fixed_count += 1
    elif task_count < 3:
        # Delete all and recreate
        cursor.execute('DELETE FROM task WHERE day_id = ?', (day_id,))
        
        tasks = get_default_tasks(day_focus, day_num)
        for hour, (title, prompt) in enumerate(tasks, 1):
            cursor.execute('''
                INSERT INTO task (title, ai_prompt, week_id, day_id, hour_number, status,
                                 status_updated_at, total_work_seconds, total_break_seconds, total_pause_seconds)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, 0, 0, 0)
            ''', (title, prompt, week_id, day_id, hour, now))
        fixed_count += 1
        
    if fixed_count <= 15:
        print(f"Fixed W{week_num}D{day_num}: {task_count} -> 3 tasks")

conn.commit()

print(f"\nFixed {fixed_count} days")

# Verify final counts
cursor.execute('SELECT COUNT(*) FROM task')
total = cursor.fetchone()[0]
expected = 497 * 3  # 497 days * 3 tasks
print(f"\nTotal tasks: {total} (expected: {expected})")

# Check per-week counts
print("\n📊 Tasks per Week (showing issues only):")
cursor.execute('''
    SELECT w.number, COUNT(t.id)
    FROM week w
    LEFT JOIN task t ON t.week_id = w.id
    GROUP BY w.id
    HAVING COUNT(t.id) != 21
    ORDER BY w.number
''')
for week_num, count in cursor.fetchall():
    print(f"  Week {week_num}: {count} tasks (should be 21)")

conn.close()
print("\nDone!")
