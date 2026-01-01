#!/usr/bin/env python3
"""Fix task-day alignment - ensure tasks match their parent day's focus topic."""

import sqlite3
from datetime import datetime

db_path = '/home/nani/.local/share/embedded-tracker/embedded_tracker.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("FIXING TASK-DAY ALIGNMENT")
print("=" * 80)

# Task templates for each day focus keyword
TASK_TEMPLATES = {
    # Week 0 - Pre-Requisite Topics
    'variables': [
        ('Declare and initialize variables in C', 'Explain C variable types: int, char, float, double'),
        ('Practice variable scope rules', 'Describe local vs global variable scope'),
        ('Complete variable exercises', 'Write a program demonstrating variable initialization')
    ],
    'loops': [
        ('Implement for loops in C', 'Write for loop examples with break and continue'),
        ('Practice while and do-while loops', 'Compare while vs do-while behavior'),
        ('Nested loop exercises', 'Implement nested loops for pattern printing')
    ],
    'functions': [
        ('Write functions with parameters', 'Explain function prototypes and definitions'),
        ('Practice function return values', 'Write functions returning different data types'),
        ('Understand function call stack', 'Trace function calls with stack diagram')
    ],
    'pointers': [
        ('Understand pointer basics', 'Explain pointer declaration and dereferencing'),
        ('Pointer arithmetic exercises', 'Practice pointer increment and array access'),
        ('Pass by reference using pointers', 'Write swap function using pointers')
    ],
    'memory': [
        ('Understand stack vs heap', 'Explain memory layout: text, data, bss, heap, stack'),
        ('Practice malloc and free', 'Write dynamic memory allocation examples'),
        ('Memory leak detection', 'Use valgrind to find memory leaks')
    ],
    'voltage': [
        ('Learn voltage fundamentals', 'Explain voltage as electrical potential difference'),
        ('Calculate voltage in circuits', 'Apply Kirchhoffs voltage law'),
        ('Measure voltage with multimeter', 'Learn multimeter voltage measurement techniques')
    ],
    'current': [
        ('Understand current flow', 'Explain current as electron flow rate'),
        ('Apply Kirchhoffs current law', 'Practice current calculations at nodes'),
        ('Measure current safely', 'Learn series ammeter connection technique')
    ],
    'ohm': [
        ('Apply Ohms Law V=IR', 'Calculate V=IR for various circuit problems'),
        ('Practice resistance calculations', 'Determine resistance from color codes'),
        ('Combine Ohms law with Kirchhoff', 'Solve complex circuit problems')
    ],
    'resistor': [
        ('Read resistor color codes', 'Learn 4-band and 5-band color code systems'),
        ('Calculate series resistors', 'Practice series resistance R_total = R1 + R2'),
        ('Calculate parallel resistors', 'Practice parallel resistance formula')
    ],
    'capacitor': [
        ('Understand capacitor basics', 'Explain capacitance, charge storage, and unit Farad'),
        ('Calculate RC time constant', 'Practice tau = RC calculations'),
        ('Capacitor charging curves', 'Analyze exponential charging behavior')
    ],
    'led': [
        ('Calculate LED current limiting resistor', 'Determine resistor value for LED circuit'),
        ('Wire LED circuits correctly', 'Connect LED with proper polarity'),
        ('LED brightness control', 'Vary LED brightness with resistor values')
    ],
    'linux': [
        ('Navigate Linux filesystem', 'Practice cd, ls, pwd, mkdir commands'),
        ('File operations in terminal', 'Use cp, mv, rm, cat, nano commands'),
        ('Understand file permissions', 'Practice chmod and file ownership')
    ],
    'terminal': [
        ('Master bash commands', 'Learn pipe, grep, find, and redirects'),
        ('Environment variables', 'Set and use PATH and custom variables'),
        ('Shell scripting basics', 'Write simple bash scripts')
    ],
    'gcc': [
        ('Compile C programs with gcc', 'Use gcc -o to compile executables'),
        ('Understand compilation stages', 'Learn preprocessing, compiling, assembling, linking'),
        ('Debug with gcc flags', 'Use -Wall, -Wextra, -g for better debugging')
    ],
    'makefile': [
        ('Write basic Makefile', 'Create Makefile with target, dependencies, commands'),
        ('Use variables in Makefile', 'Define CC, CFLAGS, and automatic variables'),
        ('Phony targets and clean', 'Implement clean target and .PHONY')
    ],
    'binary': [
        ('Convert decimal to binary', 'Practice binary conversion by hand'),
        ('Binary arithmetic', 'Add and subtract binary numbers'),
        ('Understand bit positions', 'Calculate place values for binary digits')
    ],
    'hexadecimal': [
        ('Convert hex to decimal', 'Practice hexadecimal conversion'),
        ('Hex in memory addresses', 'Understand why hex is used for addresses'),
        ('Hex and binary relationship', 'Convert between hex and binary')
    ],
    'complement': [
        ('Understand twos complement', 'Convert negative numbers to twos complement'),
        ('Twos complement arithmetic', 'Add positive and negative numbers'),
        ('Overflow detection', 'Identify overflow in signed arithmetic')
    ],
    'c program': [
        ('Write Hello World in C', 'Create and compile first C program'),
        ('Understand main function', 'Explain argc, argv, and return codes'),
        ('Use printf and scanf', 'Practice formatted I/O operations')
    ]
}

# Default template for unmatched focuses
DEFAULT_TEMPLATE = [
    ('Study {topic} fundamentals', 'Explain core concepts of {topic}'),
    ('Practice {topic} exercises', 'Complete hands-on exercises for {topic}'),
    ('Apply {topic} knowledge', 'Build small project demonstrating {topic}')
]

now = datetime.now().isoformat()

# Get all days with their focus and week number
cursor.execute('''
    SELECT d.id, d.number, d.focus, w.number as week_num, w.focus as week_focus
    FROM dayplan d
    JOIN week w ON d.week_id = w.id
    ORDER BY w.number, d.number
''')
days = cursor.fetchall()

fixed_count = 0
for day_id, day_num, day_focus, week_num, week_focus in days:
    if not day_focus:
        continue
    
    # Get current tasks for this day
    cursor.execute('SELECT id, title FROM task WHERE day_id = ?', (day_id,))
    current_tasks = cursor.fetchall()
    
    # Check if tasks are misaligned
    day_focus_lower = day_focus.lower()
    needs_fix = False
    
    for task_id, task_title in current_tasks:
        task_lower = task_title.lower()
        # Check if task contains wrong week reference
        expected_prefix = f'[w{week_num}d'
        if '[w' in task_lower and expected_prefix not in task_lower:
            needs_fix = True
            break
        # Check for advanced topics in beginner weeks
        if week_num <= 5:  # Early weeks should be basic
            advanced_keywords = ['fft', 'pid', 'kalman', 'cache', 'lock-free', 'fixed-point']
            if any(adv in task_lower for adv in advanced_keywords):
                needs_fix = True
                break
    
    if not needs_fix:
        continue
    
    # Find matching template
    matched_template = None
    for keyword, template in TASK_TEMPLATES.items():
        if keyword in day_focus_lower:
            matched_template = template
            break
    
    if not matched_template:
        # Use default with topic substitution
        topic = day_focus.split('–')[-1].strip() if '–' in day_focus else day_focus
        matched_template = [(t[0].format(topic=topic), t[1].format(topic=topic)) for t in DEFAULT_TEMPLATE]
    
    # Delete misaligned tasks
    cursor.execute('DELETE FROM task WHERE day_id = ?', (day_id,))
    
    # Get week_id
    cursor.execute('SELECT week_id FROM dayplan WHERE id = ?', (day_id,))
    week_id = cursor.fetchone()[0]
    
    # Insert aligned tasks
    for hour_num, (title, ai_prompt) in enumerate(matched_template, 1):
        cursor.execute('''
            INSERT INTO task (title, ai_prompt, week_id, day_id, hour_number, status, 
                             status_updated_at, total_work_seconds, total_break_seconds, total_pause_seconds)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, 0, 0, 0)
        ''', (title, ai_prompt, week_id, day_id, hour_num, now))
    
    fixed_count += 1
    if fixed_count <= 15:
        print(f'Fixed W{week_num}D{day_num}: {day_focus[:40]}...')

print(f'\nFixed {fixed_count} days with misaligned tasks')

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM task')
total_tasks = cursor.fetchone()[0]
print(f'Total tasks now: {total_tasks}')

# Sample Week 0 again
print('\n📊 Week 0 After Fix:')
cursor.execute('''
    SELECT d.number, d.focus, t.title
    FROM task t
    JOIN dayplan d ON t.day_id = d.id
    JOIN week w ON t.week_id = w.id
    WHERE w.number = 0
    ORDER BY d.number, t.hour_number
''')
for day_num, day_focus, task_title in cursor.fetchall():
    print(f'  D{day_num}: {task_title[:50]}')

conn.close()
print('\nDone!')
