#!/usr/bin/env python3
"""
Export ALL data from the Embedded Systems Tracker database to CSV files for manual audit.
Exports every field of every record for line-by-line verification.
"""

import csv
import os
from pathlib import Path
from datetime import datetime

from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import (
    Phase, Week, DayPlan, Task, Resource, Project, 
    Certification, Application, HardwareItem, Metric
)
from sqlmodel import select, col

# Initialize database
init_db()

# Create output directory
OUTPUT_DIR = Path("/home/nani/Videos/embedded-tracker/audit_data")
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("📤 EXPORTING ALL DATA FOR AUDIT")
print(f"Output directory: {OUTPUT_DIR}")
print("=" * 70)

def export_to_csv(filename, headers, rows):
    """Write rows to CSV file."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"✅ Exported {len(rows)} rows to {filename}")
    return len(rows)

total_rows = 0

with session_scope() as session:
    
    # =========================================================================
    # 1. PHASES
    # =========================================================================
    phases = session.exec(select(Phase).order_by(Phase.id)).all()
    headers = ["ID", "Name", "Description", "Start Date", "End Date", "Status"]
    rows = [
        [p.id, p.name, p.description, p.start_date, p.end_date, getattr(p, 'status', 'N/A')]
        for p in phases
    ]
    total_rows += export_to_csv("01_phases.csv", headers, rows)
    
    # =========================================================================
    # 2. WEEKS
    # =========================================================================
    weeks = session.exec(select(Week).order_by(Week.number)).all()
    # Get phase names for reference
    phase_map = {p.id: p.name for p in phases}
    
    headers = ["ID", "Week Number", "Phase ID", "Phase Name", "Focus", "Start Date", "End Date"]
    rows = [
        [w.id, w.number, w.phase_id, phase_map.get(w.phase_id, "Unknown"), w.focus, w.start_date, w.end_date]
        for w in weeks
    ]
    total_rows += export_to_csv("02_weeks.csv", headers, rows)
    
    # =========================================================================
    # 3. DAYS
    # =========================================================================
    days = session.exec(select(DayPlan).order_by(DayPlan.id)).all()
    week_map = {w.id: w.number for w in weeks}
    
    headers = ["ID", "Day Number", "Week ID", "Week Number", "Focus", "Scheduled Date", "Notes"]
    rows = [
        [d.id, d.number, d.week_id, week_map.get(d.week_id, "?"), d.focus, d.scheduled_date, d.notes]
        for d in days
    ]
    total_rows += export_to_csv("03_days.csv", headers, rows)
    
    # =========================================================================
    # 4. TASKS (Hours)
    # =========================================================================
    tasks = session.exec(select(Task).order_by(Task.id)).all()
    day_map = {d.id: d.number for d in days}
    
    headers = ["ID", "Title", "Description", "AI Prompt", "Day ID", "Day Number", "Week ID", 
               "Week Number", "Hour Number", "Status", "Estimated Hours"]
    rows = []
    for t in tasks:
        week_num = week_map.get(t.week_id, "?")
        day_num = day_map.get(t.day_id, "?") if t.day_id else "N/A"
        rows.append([
            t.id, t.title, t.description, t.ai_prompt, t.day_id, day_num, 
            t.week_id, week_num, t.hour_number, t.status.value if t.status else "pending",
            t.estimated_hours
        ])
    total_rows += export_to_csv("04_tasks.csv", headers, rows)
    
    # =========================================================================
    # 5. RESOURCES (Critical for URL audit)
    # =========================================================================
    resources = session.exec(select(Resource).order_by(Resource.id)).all()
    
    headers = ["ID", "Title", "Type", "URL", "Week ID", "Week Number", "Notes"]
    rows = []
    for r in resources:
        week_num = week_map.get(r.week_id, "?")
        rows.append([
            r.id, r.title, r.type.value if r.type else "other", r.url, 
            r.week_id, week_num, r.notes
        ])
    total_rows += export_to_csv("05_resources.csv", headers, rows)
    
    # =========================================================================
    # 6. PROJECTS
    # =========================================================================
    projects = session.exec(select(Project).order_by(Project.id)).all()
    
    headers = ["ID", "Name", "Description", "Status", "Phase ID", "Phase Name", 
               "Start Date", "Due Date", "Repo URL", "Demo URL"]
    rows = []
    for p in projects:
        phase_name = phase_map.get(p.phase_id, "Unknown") if p.phase_id else "N/A"
        rows.append([
            p.id, p.name, p.description, p.status.value if p.status else "planned",
            p.phase_id, phase_name, p.start_date, p.due_date, p.repo_url, p.demo_url
        ])
    total_rows += export_to_csv("06_projects.csv", headers, rows)
    
    # =========================================================================
    # 7. CERTIFICATIONS
    # =========================================================================
    certs = session.exec(select(Certification).order_by(Certification.id)).all()
    
    headers = ["ID", "Name", "Provider", "Status", "Progress", "Phase ID", "Phase Name",
               "Due Date", "Completion Date", "Credential URL"]
    rows = []
    for c in certs:
        phase_name = phase_map.get(c.phase_id, "Unknown") if c.phase_id else "N/A"
        rows.append([
            c.id, c.name, c.provider, c.status.value if c.status else "planned",
            c.progress, c.phase_id, phase_name, c.due_date, c.completion_date, c.credential_url
        ])
    total_rows += export_to_csv("07_certifications.csv", headers, rows)
    
    # =========================================================================
    # 8. APPLICATIONS (Job Applications)
    # =========================================================================
    apps = session.exec(select(Application).order_by(Application.id)).all()
    
    headers = ["ID", "Company", "Role", "Status", "Source", "Date Applied", "Next Action", "Notes"]
    rows = [
        [a.id, a.company, a.role, a.status.value if a.status else "draft", 
         a.source, a.date_applied, a.next_action, a.notes]
        for a in apps
    ]
    total_rows += export_to_csv("08_applications.csv", headers, rows)
    
    # =========================================================================
    # 9. HARDWARE INVENTORY
    # =========================================================================
    hardware = session.exec(select(HardwareItem).order_by(HardwareItem.id)).all()
    
    headers = ["ID", "Name", "Category", "Type", "MCU", "Architecture", "Quantity", 
               "Status", "Price (INR)", "Interface", "Features", "Notes"]
    rows = []
    for h in hardware:
        rows.append([
            h.id, h.name, h.category.value if h.category else "other", 
            h.hardware_type, h.mcu, h.architecture, h.quantity,
            h.status.value if h.status else "available", h.price_inr, 
            h.interface, h.features, h.notes
        ])
    total_rows += export_to_csv("09_hardware.csv", headers, rows)
    
    # =========================================================================
    # 10. METRICS
    # =========================================================================
    metrics = session.exec(select(Metric).order_by(Metric.id)).all()
    
    headers = ["ID", "Recorded Date", "Type", "Value", "Unit", "Phase ID", "Phase Name"]
    rows = []
    for m in metrics:
        phase_name = phase_map.get(m.phase_id, "Unknown") if m.phase_id else "N/A"
        rows.append([
            m.id, m.recorded_date, m.metric_type, m.value, m.unit,
            m.phase_id, phase_name
        ])
    total_rows += export_to_csv("10_metrics.csv", headers, rows)
    
    # =========================================================================
    # 11. TASK RECORDS (Pomodoro/Time Tracking)
    # =========================================================================
    try:
        records = session.exec(select(TaskRecord).order_by(TaskRecord.id)).all()
        
        headers = ["ID", "Task ID", "Task Title", "Start Time", "End Time", 
                   "Work Seconds", "Break Seconds", "Pause Seconds", "Notes"]
        rows = []
        task_title_map = {t.id: t.title for t in tasks}
        for r in records:
            rows.append([
                r.id, r.task_id, task_title_map.get(r.task_id, "Unknown"),
                r.start_time, r.end_time, r.work_seconds, r.break_seconds, 
                r.pause_seconds, r.notes
            ])
        total_rows += export_to_csv("11_task_records.csv", headers, rows)
    except Exception as e:
        print(f"⚠️ Could not export task records: {e}")

print("\n" + "=" * 70)
print(f"📊 EXPORT COMPLETE")
print(f"Total rows exported: {total_rows}")
print(f"Output directory: {OUTPUT_DIR}")
print("=" * 70)

# Create a summary file
summary_path = OUTPUT_DIR / "00_AUDIT_SUMMARY.txt"
with open(summary_path, 'w') as f:
    f.write("EMBEDDED SYSTEMS TRACKER - DATA AUDIT EXPORT\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Total Rows: {total_rows}\n\n")
    f.write("FILES:\n")
    f.write("  01_phases.csv        - Learning phases\n")
    f.write("  02_weeks.csv         - Weekly curriculum\n")
    f.write("  03_days.csv          - Daily schedules\n")
    f.write("  04_tasks.csv         - Hourly tasks with AI prompts\n")
    f.write("  05_resources.csv     - URLs and learning materials\n")
    f.write("  06_projects.csv      - Portfolio projects\n")
    f.write("  07_certifications.csv- Certification tracking\n")
    f.write("  08_applications.csv  - Job applications\n")
    f.write("  09_hardware.csv      - Hardware inventory\n")
    f.write("  10_metrics.csv       - Progress metrics\n")
    f.write("  11_task_records.csv  - Time tracking records\n")
    f.write("\nAUDIT CHECKLIST:\n")
    f.write("  [ ] Verify all URLs in 05_resources.csv are valid\n")
    f.write("  [ ] Check week focuses match phase descriptions\n")
    f.write("  [ ] Ensure no forbidden content (web dev, video editing)\n")
    f.write("  [ ] Confirm 50+ LPA skills coverage\n")
    f.write("  [ ] Validate hardware items are embedded-relevant\n")

print(f"\n📝 Created summary file: {summary_path}")
print("\n🎯 Next Steps:")
print("   1. Open audit_data/ folder in file manager")
print("   2. Open CSV files in LibreOffice Calc or Google Sheets")
print("   3. Review each file line by line")
print("   4. Pay special attention to 05_resources.csv (URLs)")
