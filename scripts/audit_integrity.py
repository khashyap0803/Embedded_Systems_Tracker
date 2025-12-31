import json
import sys

def audit_integrity():
    print("Loading roadmap data...")
    try:
        with open('embedded_tracker/data/roadmap_seed.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: embedded_tracker/data/roadmap_seed.json not found.")
        return

    issues = []
    
    # ---------------------------------------------------------
    # PART 2: COLUMN SYNC VERIFICATION
    # ---------------------------------------------------------
    print("Checking Phase consistency...")
    phases = data.get('phases', [])
    for i, phase in enumerate(phases):
        # Rule: Name must describe outcomes (simple heuristic: length)
        if len(phase.get('description', '')) < 10:
            issues.append(f"[Phase {i+1}] Description too short: {phase.get('description')}")
        
        # Rule: Start < End date (if hardcoded, otherwise logical check)
        # (Skipping date parsing for seed data as they are often relative or placeholders, 
        # but checking Weeks are sequential)
        
        weeks = phase.get('weeks', [])
        expected_week_num = weeks[0]['number'] if weeks else 0
        
        for w_idx, week in enumerate(weeks):
            # Rule: Sequential weeks
            if week['number'] != expected_week_num:
                issues.append(f"[Phase {phase['name']}] Gap in week numbering. Expected {expected_week_num}, found {week['number']}")
            expected_week_num += 1
            
            # Key Audit: Week 0 Presence
            if week['number'] == 0:
                print("✅ Week 0 found.")
            
            # Rule: Tasks have AI prompts
            for day in week.get('days', []):
                 for hour in day.get('hours', []): # Hours structure in seed
                    if not hour.get('ai_prompt') or len(hour.get('ai_prompt')) < 5:
                         issues.append(f"[Week {week['number']}] Task '{hour.get('title')}' missing valid AI Prompt")

    # ---------------------------------------------------------
    # PART 4: 50+ LPA JOB ALIGNMENT (Keyword Search)
    # ---------------------------------------------------------
    print("Checking Skill Coverage...")
    all_text = json.dumps(data).lower()
    
    required_skills = [
        "cortex-m", "freertos", "zephyr", "i2c", "spi", "uart", "can",
        "usb", "ble", "ethernet", "jtag", "gdb", "git", "memory", 
        "power", "secure boot", "tinyml", "linux", "autosar", "iso 26262", "misra"
    ]
    
    missing_skills = []
    for skill in required_skills:
        if skill not in all_text:
            missing_skills.append(skill)
            
    if missing_skills:
        issues.append(f"❌ MISSING CRITICAL SKILLS: {', '.join(missing_skills)}")
    else:
        print("✅ All keyword skills found (preliminary check).")

    # ---------------------------------------------------------
    # SPECIAL VALIDATION RULES
    # ---------------------------------------------------------
    forbidden = ["davinci resolve", "html", "css", "android studio"]
    for bad in forbidden:
        if bad in all_text:
            issues.append(f"❌ FORBIDDEN CONTENT FOUND: {bad}")

    print("\n" + "="*50)
    print("DATA INTEGRITY AUDIT RESULTS")
    print("="*50)
    
    if issues:
        print(f"Found {len(issues)} logic/integrity issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("✅ Logic & Integrity Checks Passed.")

if __name__ == "__main__":
    audit_integrity()
