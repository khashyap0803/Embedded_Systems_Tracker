#!/usr/bin/env python3
"""
Complete Curriculum Realignment - Stanford/MIT/IIT/Oxford Standards
Regenerates ALL tasks to properly match their parent day focus topics.
"""

import sqlite3
from datetime import datetime
import re

db_path = '/home/nani/.local/share/embedded-tracker/embedded_tracker.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

now = datetime.now().isoformat()

print("=" * 80)
print("COMPLETE CURRICULUM REALIGNMENT - STANFORD/MIT/IIT/OXFORD STANDARDS")
print("=" * 80)

# Comprehensive topic-to-tasks mapping
# Each topic keyword maps to 3 properly aligned tasks
TOPIC_TASKS = {
    # C Programming Fundamentals
    'variable': [
        ('C Data Types and Variable Declaration', 'Explain int, char, float, double, and their memory sizes'),
        ('Variable Scope and Lifetime', 'Describe local, global, static, and extern variables'),
        ('Constants and Type Qualifiers', 'Use const, volatile, and typedef effectively')
    ],
    'loop': [
        ('For Loop Mastery', 'Implement for loops with break, continue, and nested structures'),
        ('While and Do-While Patterns', 'Compare while vs do-while for different use cases'),
        ('Loop Optimization Techniques', 'Avoid common pitfalls and optimize loop performance')
    ],
    'function': [
        ('Function Prototypes and Definitions', 'Write function declarations and implementations'),
        ('Parameter Passing Methods', 'Compare pass-by-value vs pass-by-pointer'),
        ('Recursive Functions', 'Implement recursion with proper base cases')
    ],
    'pointer': [
        ('Pointer Fundamentals', 'Declare, initialize, and dereference pointers'),
        ('Pointer Arithmetic', 'Navigate arrays and memory using pointer math'),
        ('Function Pointers', 'Implement callbacks using function pointers')
    ],
    'memory': [
        ('Stack vs Heap Memory', 'Understand memory layout: text, data, bss, heap, stack'),
        ('Dynamic Memory Management', 'Use malloc, calloc, realloc, and free correctly'),
        ('Memory Debugging', 'Detect leaks and errors with valgrind')
    ],
    'struct': [
        ('Structure Definition and Usage', 'Define structs with various member types'),
        ('Nested Structures and Arrays', 'Create complex data structures'),
        ('Bit Fields and Alignment', 'Optimize memory with bit fields and packing')
    ],
    
    # Electronics Fundamentals
    'voltage': [
        ('Voltage Fundamentals', 'Understand voltage as electrical potential difference'),
        ('Kirchhoff Voltage Law', 'Apply KVL to analyze series circuits'),
        ('Voltage Measurement', 'Use multimeter for accurate voltage readings')
    ],
    'current': [
        ('Current Flow Principles', 'Understand current as charge flow rate'),
        ('Kirchhoff Current Law', 'Apply KCL to analyze node currents'),
        ('Current Measurement', 'Safely measure current with ammeter')
    ],
    'ohm': [
        ('Ohms Law Application', 'Calculate V=IR for circuit analysis'),
        ('Resistance Combinations', 'Compute series and parallel resistances'),
        ('Power Calculations', 'Use P=IV and P=I²R for power analysis')
    ],
    'resistor': [
        ('Resistor Color Codes', 'Read 4-band and 5-band resistor values'),
        ('Resistor Networks', 'Analyze series, parallel, and mixed networks'),
        ('Power Ratings', 'Select resistors based on power dissipation')
    ],
    'capacitor': [
        ('Capacitor Fundamentals', 'Understand capacitance and charge storage'),
        ('RC Time Constants', 'Calculate charging and discharging curves'),
        ('Capacitor Applications', 'Use capacitors for filtering and decoupling')
    ],
    'led': [
        ('LED Characteristics', 'Understand forward voltage and current limits'),
        ('Current Limiting Design', 'Calculate resistor values for LED circuits'),
        ('LED Driver Circuits', 'Design constant-current LED drivers')
    ],
    'transistor': [
        ('BJT Fundamentals', 'Understand NPN/PNP operation and biasing'),
        ('MOSFET Basics', 'Compare enhancement vs depletion mode'),
        ('Switching Applications', 'Design transistor switches for loads')
    ],
    
    # Linux and Tools
    'linux': [
        ('Linux Command Line Basics', 'Navigate filesystem with cd, ls, pwd'),
        ('File Operations', 'Use cp, mv, rm, cat, and redirections'),
        ('Text Processing', 'Apply grep, sed, awk for text manipulation')
    ],
    'terminal': [
        ('Shell Environment', 'Configure PATH, aliases, and environment variables'),
        ('Process Management', 'Use ps, top, kill, and job control'),
        ('Shell Scripting', 'Write bash scripts for automation')
    ],
    'gcc': [
        ('GCC Compilation Process', 'Understand preprocessing, compiling, linking'),
        ('Compiler Flags', 'Use -Wall, -Wextra, -O2, -g for quality'),
        ('Cross-Compilation', 'Configure GCC for ARM targets')
    ],
    'makefile': [
        ('Makefile Fundamentals', 'Define targets, dependencies, and rules'),
        ('Variables and Patterns', 'Use automatic variables and pattern rules'),
        ('Build Automation', 'Implement clean, all, and install targets')
    ],
    'git': [
        ('Git Basics', 'Initialize, add, commit, and push changes'),
        ('Branching Strategy', 'Use feature branches and merge workflows'),
        ('Collaboration', 'Handle pull requests and code reviews')
    ],
    
    # Number Systems
    'binary': [
        ('Binary Number System', 'Convert between decimal and binary'),
        ('Binary Arithmetic', 'Perform addition, subtraction in binary'),
        ('Bitwise Operations', 'Apply AND, OR, XOR, NOT, shifts')
    ],
    'hexadecimal': [
        ('Hexadecimal System', 'Convert hex to decimal and binary'),
        ('Memory Addresses', 'Read and interpret hex addresses'),
        ('Hex in Debugging', 'Use hex for register and memory inspection')
    ],
    'complement': [
        ('Twos Complement', 'Represent negative numbers in binary'),
        ('Signed Arithmetic', 'Perform math with signed integers'),
        ('Overflow Detection', 'Identify arithmetic overflow conditions')
    ],
    
    # ARM and MCU
    'arm': [
        ('ARM Architecture Overview', 'Understand Cortex-M processor family'),
        ('Register Set', 'Master R0-R15, PSR, and special registers'),
        ('Instruction Set', 'Learn Thumb-2 instruction encoding')
    ],
    'cortex': [
        ('Cortex-M Pipeline', 'Understand fetch-decode-execute stages'),
        ('Memory Map', 'Navigate code, SRAM, peripheral regions'),
        ('System Exceptions', 'Handle Reset, NMI, HardFault')
    ],
    'stm32': [
        ('STM32 Family Selection', 'Choose appropriate STM32 for project'),
        ('Clock Configuration', 'Configure HSE, PLL, and clock tree'),
        ('Peripheral Overview', 'Understand GPIO, timers, communication')
    ],
    'gpio': [
        ('GPIO Configuration', 'Set input, output, and alternate modes'),
        ('Pull-up/Pull-down', 'Configure internal resistors'),
        ('GPIO Speed and Drive', 'Optimize for EMI and power')
    ],
    'adc': [
        ('ADC Fundamentals', 'Understand SAR ADC operation'),
        ('ADC Configuration', 'Set resolution, sampling time, channels'),
        ('ADC with DMA', 'Continuous conversion with DMA transfer')
    ],
    'dac': [
        ('DAC Fundamentals', 'Understand DAC architecture'),
        ('Waveform Generation', 'Generate sine, triangle, sawtooth waves'),
        ('Audio Applications', 'Implement audio output with DAC')
    ],
    'pwm': [
        ('PWM Fundamentals', 'Understand duty cycle and frequency'),
        ('Timer-based PWM', 'Configure timers for PWM output'),
        ('PWM Applications', 'Motor control, LED dimming, audio')
    ],
    'timer': [
        ('Timer Architecture', 'Understand prescaler, counter, auto-reload'),
        ('Input Capture', 'Measure pulse width and frequency'),
        ('Output Compare', 'Generate precise timing events')
    ],
    'interrupt': [
        ('Interrupt Fundamentals', 'Understand IRQ, priorities, vectors'),
        ('NVIC Configuration', 'Set priorities and enable interrupts'),
        ('ISR Best Practices', 'Write efficient interrupt handlers')
    ],
    'dma': [
        ('DMA Fundamentals', 'Understand direct memory access'),
        ('DMA Configuration', 'Set source, destination, transfer size'),
        ('DMA with Peripherals', 'Link DMA to ADC, UART, SPI')
    ],
    
    # Communication Protocols
    'uart': [
        ('UART Protocol', 'Understand start, data, parity, stop bits'),
        ('UART Configuration', 'Set baud rate, word length, parity'),
        ('UART with DMA', 'Implement efficient UART transfers')
    ],
    'i2c': [
        ('I2C Protocol', 'Understand start, address, data, stop'),
        ('I2C Master Mode', 'Implement read and write transactions'),
        ('I2C Slave Mode', 'Respond to master requests')
    ],
    'spi': [
        ('SPI Protocol', 'Understand MOSI, MISO, SCK, SS signals'),
        ('SPI Modes', 'Configure CPOL and CPHA settings'),
        ('SPI with DMA', 'High-speed transfers with DMA')
    ],
    'can': [
        ('CAN Protocol', 'Understand frames, arbitration, acknowledgment'),
        ('CAN Configuration', 'Set bit timing and filters'),
        ('CAN Application', 'Implement automotive messaging')
    ],
    'usb': [
        ('USB Fundamentals', 'Understand endpoints, descriptors, classes'),
        ('USB Device Mode', 'Implement CDC, HID, or MSC class'),
        ('USB Debugging', 'Use protocol analyzers for debugging')
    ],
    'ethernet': [
        ('Ethernet Fundamentals', 'Understand MAC, PHY, and framing'),
        ('TCP/IP Stack', 'Implement lightweight TCP/IP (lwIP)'),
        ('Network Applications', 'Build HTTP server, MQTT client')
    ],
    'bluetooth': [
        ('Bluetooth Architecture', 'Understand BLE stack layers'),
        ('GATT Profile', 'Define services and characteristics'),
        ('BLE Applications', 'Implement sensor data transmission')
    ],
    'mqtt': [
        ('MQTT Protocol', 'Understand publish, subscribe, topics'),
        ('MQTT Client', 'Connect, publish, and subscribe'),
        ('MQTT Security', 'Implement TLS and authentication')
    ],
    
    # RTOS
    'rtos': [
        ('RTOS Fundamentals', 'Understand real-time scheduling concepts'),
        ('Task Management', 'Create, delete, and manage tasks'),
        ('Synchronization', 'Use semaphores, mutexes, queues')
    ],
    'freertos': [
        ('FreeRTOS Setup', 'Configure and integrate FreeRTOS'),
        ('Task Creation', 'Implement tasks with priorities'),
        ('Inter-task Communication', 'Use queues and event groups')
    ],
    'zephyr': [
        ('Zephyr Overview', 'Understand Zephyr architecture'),
        ('Device Tree', 'Configure hardware with devicetree'),
        ('Zephyr Drivers', 'Use and create device drivers')
    ],
    'scheduler': [
        ('Scheduling Algorithms', 'Understand preemptive vs cooperative'),
        ('Priority Inversion', 'Detect and prevent priority issues'),
        ('Rate Monotonic', 'Apply RMA for real-time analysis')
    ],
    'mutex': [
        ('Mutex Fundamentals', 'Protect shared resources'),
        ('Deadlock Prevention', 'Avoid circular wait conditions'),
        ('Priority Inheritance', 'Implement priority inheritance')
    ],
    'semaphore': [
        ('Semaphore Types', 'Compare binary and counting semaphores'),
        ('Semaphore Usage', 'Synchronize tasks and ISRs'),
        ('Semaphore Pitfalls', 'Avoid common semaphore errors')
    ],
    'queue': [
        ('Queue Fundamentals', 'Implement thread-safe queues'),
        ('Queue Operations', 'Send, receive with timeout'),
        ('Queue Design', 'Size queues for worst-case scenarios')
    ],
    
    # Linux Embedded
    'kernel': [
        ('Linux Kernel Overview', 'Understand kernel architecture'),
        ('Kernel Configuration', 'Use menuconfig for customization'),
        ('Kernel Modules', 'Build and load kernel modules')
    ],
    'driver': [
        ('Linux Driver Model', 'Understand device, driver, bus'),
        ('Character Drivers', 'Implement file operations'),
        ('Platform Drivers', 'Match drivers with devices')
    ],
    'yocto': [
        ('Yocto Overview', 'Understand layers, recipes, bitbake'),
        ('Custom Layers', 'Create meta-layers for projects'),
        ('Image Customization', 'Build minimal and custom images')
    ],
    'buildroot': [
        ('Buildroot Setup', 'Configure and build root filesystem'),
        ('Package Selection', 'Add and configure packages'),
        ('Board Support', 'Create board-specific configurations')
    ],
    'device tree': [
        ('Device Tree Syntax', 'Understand nodes and properties'),
        ('Device Tree Overlays', 'Apply runtime modifications'),
        ('Device Tree Debugging', 'Verify device tree correctness')
    ],
    
    # Automotive
    'autosar': [
        ('AUTOSAR Architecture', 'Understand Classic and Adaptive platforms'),
        ('Software Components', 'Design SWC with ports and interfaces'),
        ('RTE Configuration', 'Configure runtime environment')
    ],
    'iso 26262': [
        ('Functional Safety Overview', 'Understand ASIL levels A-D'),
        ('Safety Analysis', 'Perform FMEA and FTA'),
        ('Safety Requirements', 'Derive safety requirements')
    ],
    'fmea': [
        ('FMEA Fundamentals', 'Failure Mode and Effects Analysis'),
        ('Risk Priority Number', 'Calculate and prioritize risks'),
        ('FMEA Documentation', 'Create comprehensive FMEA tables')
    ],
    
    # AI/ML Edge
    'tinyml': [
        ('TinyML Overview', 'Understand ML on microcontrollers'),
        ('Model Optimization', 'Apply quantization and pruning'),
        ('TFLite Micro', 'Deploy models with TensorFlow Lite Micro')
    ],
    'inference': [
        ('Inference Pipeline', 'Preprocess, infer, postprocess'),
        ('Performance Optimization', 'Optimize latency and memory'),
        ('Model Validation', 'Verify accuracy on embedded device')
    ],
    'neural': [
        ('Neural Network Basics', 'Understand layers and activations'),
        ('CNN for Vision', 'Apply convolutional networks'),
        ('RNN for Time Series', 'Process sequential data')
    ],
    
    # Security
    'security': [
        ('Embedded Security Basics', 'Understand threat models'),
        ('Secure Coding', 'Avoid vulnerabilities in C'),
        ('Security Testing', 'Perform penetration testing')
    ],
    'crypto': [
        ('Cryptography Fundamentals', 'Symmetric vs asymmetric encryption'),
        ('Hardware Crypto', 'Use crypto accelerators'),
        ('Key Management', 'Secure key storage and rotation')
    ],
    'secure boot': [
        ('Secure Boot Chain', 'Verify bootloader and firmware'),
        ('Code Signing', 'Sign firmware images'),
        ('Attestation', 'Implement device attestation')
    ],
    
    # Testing and Debugging
    'test': [
        ('Unit Testing', 'Write tests with Unity or CppUTest'),
        ('Integration Testing', 'Test component interactions'),
        ('Test Automation', 'Automate test execution')
    ],
    'debug': [
        ('Debugging Techniques', 'Use printf, assertions, breakpoints'),
        ('GDB Usage', 'Set breakpoints, watch variables'),
        ('Core Dump Analysis', 'Analyze crash dumps')
    ],
    'jtag': [
        ('JTAG Fundamentals', 'Understand TAP, TDI, TDO, TCK'),
        ('JTAG Debugging', 'Connect and debug with JTAG'),
        ('Boundary Scan', 'Test PCB connections with JTAG')
    ],
    'profiling': [
        ('CPU Profiling', 'Identify performance bottlenecks'),
        ('Memory Profiling', 'Track memory usage patterns'),
        ('Power Profiling', 'Measure current consumption')
    ],
    
    # DSP and Math
    'dsp': [
        ('DSP Fundamentals', 'Understand sampling and filtering'),
        ('FIR Filters', 'Design and implement FIR filters'),
        ('IIR Filters', 'Design and implement IIR filters')
    ],
    'fft': [
        ('FFT Fundamentals', 'Understand frequency domain analysis'),
        ('FFT Implementation', 'Implement radix-2 FFT'),
        ('FFT Applications', 'Apply FFT for spectrum analysis')
    ],
    'fixed-point': [
        ('Fixed-Point Arithmetic', 'Understand Q-format representation'),
        ('Fixed-Point Operations', 'Implement multiply, divide'),
        ('Fixed-Point Libraries', 'Use CMSIS-DSP fixed-point functions')
    ],
    'pid': [
        ('PID Control Theory', 'Understand P, I, D components'),
        ('PID Tuning', 'Apply Ziegler-Nichols or manual tuning'),
        ('PID Implementation', 'Implement discrete-time PID')
    ],
    'kalman': [
        ('Kalman Filter Theory', 'Understand state estimation'),
        ('Kalman Implementation', 'Implement 1D and multi-dim filters'),
        ('Sensor Fusion', 'Combine accelerometer and gyroscope')
    ],
    
    # Bootloader and OTA
    'bootloader': [
        ('Bootloader Architecture', 'Understand boot process'),
        ('Dual-Bank Update', 'Implement A/B partition scheme'),
        ('Bootloader Security', 'Verify firmware signatures')
    ],
    'ota': [
        ('OTA Architecture', 'Design over-the-air update system'),
        ('Delta Updates', 'Implement differential updates'),
        ('OTA Rollback', 'Handle failed updates safely')
    ],
    
    # Power Management
    'power': [
        ('Power Analysis', 'Measure and analyze power consumption'),
        ('Low Power Design', 'Minimize active and standby power'),
        ('Battery Management', 'Implement charging and monitoring')
    ],
    'sleep': [
        ('Sleep Modes', 'Understand stop, standby, shutdown'),
        ('Wake Sources', 'Configure RTC, GPIO, peripheral wakeup'),
        ('Sleep Optimization', 'Minimize wake latency and power')
    ],
    
    # Hardware Design
    'pcb': [
        ('PCB Design Basics', 'Understand schematic to layout flow'),
        ('PCB Layout Rules', 'Apply routing and clearance rules'),
        ('PCB Manufacturing', 'Generate gerbers and BOM')
    ],
    'schematic': [
        ('Schematic Capture', 'Create schematics with symbols'),
        ('Power Supply Design', 'Design regulators and decoupling'),
        ('Signal Integrity', 'Apply termination and shielding')
    ],
    
    # Default fallback for simulation, integration, etc.
    'simulation': [
        ('Simulation Setup', 'Configure simulation environment'),
        ('Simulation Execution', 'Run and analyze simulations'),
        ('Simulation Validation', 'Verify against real hardware')
    ],
    'integration': [
        ('Integration Planning', 'Define integration strategy'),
        ('Integration Testing', 'Test component interactions'),
        ('Integration Review', 'Document and review results')
    ],
    'portfolio': [
        ('Portfolio Project Planning', 'Define project scope and goals'),
        ('Portfolio Implementation', 'Build demonstrable project'),
        ('Portfolio Documentation', 'Create professional documentation')
    ],
    'review': [
        ('Code Review', 'Perform thorough code review'),
        ('Design Review', 'Review architecture and design'),
        ('Documentation Review', 'Update and improve documentation')
    ],
    'rest': [
        ('Review Week Concepts', 'Consolidate learning from the week'),
        ('Practice Exercises', 'Complete additional practice problems'),
        ('Plan Next Steps', 'Prepare for upcoming topics')
    ],
    'deep': [
        ('Deep Dive Study', 'Thorough exploration of topic'),
        ('Hands-on Practice', 'Build practical examples'),
        ('Knowledge Application', 'Apply to real projects')
    ],
    'work': [
        ('Focused Work Session', 'Concentrated study time'),
        ('Practical Implementation', 'Build and test code'),
        ('Progress Review', 'Assess and document progress')
    ],
}

# Default template for unmatched focuses
def get_default_tasks(day_focus):
    """Generate tasks from day focus when no keyword matches."""
    # Clean up the focus text
    if '–' in day_focus:
        topic = day_focus.split('–')[-1].strip()
    elif '-' in day_focus:
        topic = day_focus.split('-')[-1].strip()
    else:
        topic = day_focus
    
    # Limit length
    topic = topic[:40]
    
    return [
        (f'Study {topic}', f'Learn fundamental concepts of {topic}'),
        (f'Practice {topic}', f'Complete hands-on exercises for {topic}'),
        (f'Apply {topic}', f'Build project demonstrating {topic}')
    ]


def find_matching_tasks(day_focus):
    """Find the best matching task set for a day focus."""
    if not day_focus:
        return None
    
    focus_lower = day_focus.lower()
    
    # Try to match keywords
    for keyword, tasks in TOPIC_TASKS.items():
        if keyword in focus_lower:
            return tasks
    
    return None


# Get all days with their focus
cursor.execute('''
    SELECT d.id, d.number, d.focus, d.week_id, w.number as week_num, w.focus as week_focus
    FROM dayplan d
    JOIN week w ON d.week_id = w.id
    ORDER BY w.number, d.number
''')
all_days = cursor.fetchall()

print(f"\nProcessing {len(all_days)} days...")

regenerated = 0
for day_id, day_num, day_focus, week_id, week_num, week_focus in all_days:
    # Find matching tasks
    tasks = find_matching_tasks(day_focus)
    
    if tasks is None:
        # Try matching from week focus if day focus doesn't match
        tasks = find_matching_tasks(week_focus)
    
    if tasks is None:
        # Use default based on day focus
        tasks = get_default_tasks(day_focus or f"Week {week_num} Day {day_num}")
    
    # Delete existing tasks for this day
    cursor.execute('DELETE FROM task WHERE day_id = ?', (day_id,))
    
    # Insert new aligned tasks
    for hour, (title, prompt) in enumerate(tasks, 1):
        cursor.execute('''
            INSERT INTO task (title, ai_prompt, week_id, day_id, hour_number, status,
                             status_updated_at, total_work_seconds, total_break_seconds, total_pause_seconds)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, 0, 0, 0)
        ''', (title, prompt, week_id, day_id, hour, now))
    
    regenerated += 1
    if regenerated % 50 == 0:
        print(f"  Processed {regenerated} days...")

conn.commit()

print(f"\n✅ Regenerated tasks for {regenerated} days")

# Verify counts
cursor.execute('SELECT COUNT(*) FROM task')
total_tasks = cursor.fetchone()[0]
print(f"Total tasks: {total_tasks} (expected: 1491)")

# Sample verification
print("\n" + "=" * 80)
print("SAMPLE VERIFICATION")
print("=" * 80)

for week_num in [0, 10, 20, 40, 60, 70]:
    cursor.execute('''
        SELECT d.number, d.focus, t.title
        FROM dayplan d
        JOIN week w ON d.week_id = w.id
        JOIN task t ON t.day_id = d.id
        WHERE w.number = ?
        ORDER BY d.number, t.hour_number
        LIMIT 6
    ''', (week_num,))
    results = cursor.fetchall()
    
    cursor.execute('SELECT focus FROM week WHERE number = ?', (week_num,))
    week_focus = cursor.fetchone()[0]
    
    print(f"\nWeek {week_num}: {week_focus[:50]}...")
    for day_num, day_focus, task_title in results:
        print(f"  D{day_num}: {task_title[:50]}")

conn.close()
print("\n✅ Complete curriculum realignment done!")
