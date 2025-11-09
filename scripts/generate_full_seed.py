from pathlib import Path
import json
import math
from datetime import date, timedelta
from typing import Optional


DAILY_TARGET_MINUTES = 240
MIN_SEGMENT_MINUTES = 30
STATUS_MAP = {
    "planned": "pending",
    "in_progress": "working",
    "blocked": "paused",
    "complete": "completed",
    "completed": "completed",
}


def _inject_daily_plan(seed: dict) -> None:
    for phase in seed.get("phases", []):
        for week in phase.get("weeks", []):
            if week.get("days"):
                continue
            if not week.get("tasks"):
                continue
            week["days"] = _build_week_days(week)


def _build_week_days(week: dict) -> list[dict]:
    start = date.fromisoformat(week["start_date"])
    segments = _build_hour_segments(week.get("tasks", []))
    if not segments:
        return []

    days: list[dict] = []
    current_segments: list[dict] = []
    current_minutes = 0
    for segment in segments:
        if current_segments and current_minutes + segment["estimated_minutes"] > DAILY_TARGET_MINUTES:
            days.append(_compose_day(len(days), start, current_segments))
            current_segments = []
            current_minutes = 0
        current_segments.append(segment)
        current_minutes += segment["estimated_minutes"]

    if current_segments:
        days.append(_compose_day(len(days), start, current_segments))

    next_hour_number = segments[-1]["hour_number"] + 1
    while len(days) < 7:
        buffer_segment = {
            "hour_number": next_hour_number,
            "title": "Review & integration block",
            "description": "Reflect on progress, consolidate notes, and plan for upcoming tasks.",
            "estimated_minutes": 60,
            "status": "pending",
            "ai_prompt": "Summarize the key insights learned this week and list open questions for tomorrow.",
            "source_task_title": "Weekly reflection",
        }
        days.append(_compose_day(len(days), start, [buffer_segment], buffer=True))
        next_hour_number += 1

    return days


def _build_hour_segments(tasks: list[dict]) -> list[dict]:
    segments: list[dict] = []
    next_hour_number = 1
    for task in tasks:
        total_minutes = task.get("estimated_minutes")
        if total_minutes is None:
            estimated_hours = task.get("estimated_hours")
            if estimated_hours is None:
                estimated_hours = 1.0
            total_minutes = max(MIN_SEGMENT_MINUTES, int(float(estimated_hours) * 60))
        else:
            total_minutes = max(MIN_SEGMENT_MINUTES, int(total_minutes))

        segments_count = max(1, math.ceil(total_minutes / 60))
        base_minutes = total_minutes // segments_count
        remainder = total_minutes % segments_count

        for index in range(segments_count):
            minutes = base_minutes + (1 if index < remainder else 0)
            minutes = max(MIN_SEGMENT_MINUTES, minutes)
            segments.append(
                {
                    "hour_number": next_hour_number,
                    "title": task["title"]
                    if segments_count == 1
                    else f"{task['title']} (Segment {index + 1}/{segments_count})",
                    "description": task.get("description"),
                    "estimated_minutes": minutes,
                    "status": task.get("status", "pending"),
                    "ai_prompt": task.get("ai_prompt"),
                    "source_task_title": task["title"],
                }
            )
            next_hour_number += 1

    return segments


def _compose_day(index: int, week_start: date, segments: list[dict], *, buffer: bool = False) -> dict:
    scheduled = week_start + timedelta(days=min(index, 6))
    focus = "Integration & Review" if buffer else segments[0]["source_task_title"]
    notes_items = list(_unique_titles(segments))
    notes = f"Focus hours: {', '.join(notes_items)}" if notes_items else None
    return {
        "number": index + 1,
        "scheduled_date": scheduled.isoformat(),
        "focus": focus,
        "notes": notes,
        "status": "pending",
        "hours": [
            {
                "hour_number": item["hour_number"],
                "title": item["title"],
                "description": item.get("description") or item["source_task_title"],
                "estimated_minutes": item["estimated_minutes"],
                "status": item.get("status", "pending"),
                "ai_prompt": item.get("ai_prompt"),
                "source_task_title": item["source_task_title"],
            }
            for item in segments
        ],
    }


def _unique_titles(segments: list[dict]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for segment in segments:
        title = segment["source_task_title"]
        if title not in seen:
            seen.add(title)
            ordered.append(title)
    return ordered


def _normalise_status(value: Optional[str]) -> str:
    if not value:
        return "pending"
    return STATUS_MAP.get(value.lower(), value.lower())


def _harmonise_statuses(seed: dict) -> None:
    for phase in seed.get("phases", []):
        for week in phase.get("weeks", []):
            for task in week.get("tasks", []):
                task["status"] = _normalise_status(task.get("status"))
            for day in week.get("days", []):
                day["status"] = _normalise_status(day.get("status"))
                for hour in day.get("hours", []):
                    hour["status"] = _normalise_status(hour.get("status"))


def build_seed() -> dict:
    seed = {
        "phases": [
            {
                "name": "Phase 1: Ironclad Foundations",
                "description": "Electronics, digital logic, and C mastery foundations.",
                "start_date": "2025-10-26",
                "end_date": "2025-12-25",
                "weeks": [
                    {
                        "number": 1,
                        "start_date": "2025-10-26",
                        "end_date": "2025-11-01",
                        "focus": "Electronics basics kickoff (Ohm, Kirchhoff)",
                        "tasks": [
                            {
                                "title": "Watch NPTEL Basic Electronics lectures 1-2",
                                "description": "Take Notion notes using Concept | Formula | Embedded tie-in template.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Summarize Kirchhoff Voltage Law implications for MCU power rails.",
                                "status": "planned",
                            },
                            {
                                "title": "Complete 10 Ohm's Law drills in C",
                                "description": "Implement calculator variations in C and Python to verify results.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Generate a C function that computes voltage from current and resistance with input validation.",
                                "status": "planned",
                            },
                            {
                                "title": "Simulate voltage divider in Tinkercad",
                                "description": "Validate 5V to 3.3V conversion with resistor sweep.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Provide guidance for measuring simulated voltage divider output accurately.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "NPTEL Basic Electronics Lecture 1",
                                "type": "video",
                                "url": "https://youtube.com/playlist?list=NPTEL-electronics",
                                "notes": "Focus on circuit laws and measurement techniques.",
                            },
                            {
                                "title": "Concept Template Notion Page",
                                "type": "tool",
                                "url": "https://www.notion.so/embedded-concepts-template",
                                "notes": "Use for weeknight note-taking.",
                            },
                        ],
                    },
                    {
                        "number": 2,
                        "start_date": "2025-11-02",
                        "end_date": "2025-11-08",
                        "focus": "Passive component deep dive + calculator project",
                        "tasks": [
                            {
                                "title": "Study capacitors and inductors from Practical Electronics ch.2",
                                "description": "Summaries + flashcards for reactance formulas.",
                                "estimated_hours": 4.5,
                                "ai_prompt": "Explain how capacitor ESR impacts embedded power stability.",
                                "status": "planned",
                            },
                            {
                                "title": "Build voltage divider calculator script",
                                "description": "Python CLI that computes Vout and saves results to CSV.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Draft Python code for interactive voltage divider calculator with numpy.",
                                "status": "planned",
                            },
                            {
                                "title": "Publish Week 2 project log to GitHub",
                                "description": "Record 5 minute demo video and update README.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Produce a concise project summary paragraph for README.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Practical Electronics for Inventors - Chapter 2",
                                "type": "book",
                                "notes": "Review capacitor charging curves.",
                            },
                            {
                                "title": "Voltage Divider Calculator Reference",
                                "type": "article",
                                "url": "https://www.allaboutcircuits.com/tools/voltage-divider-calculator/",
                                "notes": "Cross-check CLI output.",
                            },
                        ],
                    },
                    {
                        "number": 3,
                        "start_date": "2025-11-09",
                        "end_date": "2025-11-15",
                        "focus": "Digital logic fundamentals & combinational design",
                        "tasks": [
                            {
                                "title": "Review logic gate truth tables and Boolean algebra",
                                "description": "Summarize NAND/NOR universality and create flashcards in Notion.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Generate practice problems for simplifying Boolean expressions using De Morgan's law.",
                                "status": "planned",
                            },
                            {
                                "title": "Design 4-bit adder in Logisim",
                                "description": "Implement half/full adders and verify with waveform screenshots.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Create a Logisim instruction set for chaining full adders into a 4-bit ripple adder.",
                                "status": "planned",
                            },
                            {
                                "title": "Draft FSM notes for embedded interrupts",
                                "description": "Explain how state machines map to ISR driven workflows in MCUs.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Outline an ISR-safe finite state machine template for button debouncing.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Coursera Digital Systems Week 1",
                                "type": "course",
                                "url": "https://www.coursera.org/learn/digital-systems",
                                "notes": "Work through combinational logic assignments.",
                            },
                            {
                                "title": "Logisim Evolution",
                                "type": "tool",
                                "url": "https://github.com/logisim-evolution/logisim-evolution",
                                "notes": "Use to capture FSM diagrams.",
                            },
                        ],
                    },
                    {
                        "number": 4,
                        "start_date": "2025-11-16",
                        "end_date": "2025-11-22",
                        "focus": "Sequential logic and MCU architecture overview",
                        "tasks": [
                            {
                                "title": "Complete Coursera Digital Systems Week 2 labs",
                                "description": "Simulate counters and registers; export timing screenshots.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Critique register-transfer diagrams for an 8-bit timer peripheral.",
                                "status": "planned",
                            },
                            {
                                "title": "Map AVR vs ARM architecture",
                                "description": "Create comparison table for register sets, pipeline depth, interrupt model.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Summarize how ARM Cortex-M NVIC differs from AVR interrupt handling.",
                                "status": "planned",
                            },
                            {
                                "title": "Prototype 4-bit state machine in C",
                                "description": "Use switch-case to model FSM transitions and run via gcc.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Generate a C template for an FSM controlling LED patterns with non-blocking delays.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Udemy Digital Electronics for Embedded",
                                "type": "course",
                                "url": "https://www.udemy.com/course/digital-electronics-for-embedded-systems/",
                                "notes": "Cover sequential logic sections.",
                            },
                            {
                                "title": "ARM Cortex-M Architecture Overview",
                                "type": "article",
                                "url": "https://developer.arm.com/documentation/dui0553/a/",
                                "notes": "Focus on NVIC chapter.",
                            },
                        ],
                    },
                    {
                        "number": 5,
                        "start_date": "2025-11-23",
                        "end_date": "2025-11-29",
                        "focus": "C programming foundations and toolchain setup",
                        "tasks": [
                            {
                                "title": "Finish edX C for Embedded Week 1",
                                "description": "Implement pointers and structs exercises in VS Code.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Review pointer arithmetic pitfalls with examples for MCU memory maps.",
                                "status": "planned",
                            },
                            {
                                "title": "Automate GCC build + run tasks",
                                "description": "Configure VS Code task for compiling C drills; verify debug symbols.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Provide launch.json snippet for gdb debugging C console app on Ubuntu.",
                                "status": "planned",
                            },
                            {
                                "title": "HackerRank C warmup set",
                                "description": "Solve 15 easy/medium problems and document learnings.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Suggest efficient solutions for pointer-based string reversal challenges.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "edX C for Embedded Week 1",
                                "type": "course",
                                "url": "https://www.edx.org/course/c-programming-for-embedded-systems",
                                "notes": "Download lab starter code.",
                            },
                            {
                                "title": "HackerRank Embedded C Track",
                                "type": "tool",
                                "url": "https://www.hackerrank.com/domains/tutorials/10-days-of-c",
                                "notes": "Track progress for weekly metrics.",
                            },
                        ],
                    },
                    {
                        "number": 6,
                        "start_date": "2025-11-30",
                        "end_date": "2025-12-06",
                        "focus": "Pointers, memory management, and debugging",
                        "tasks": [
                            {
                                "title": "Implement custom allocator simulator",
                                "description": "Write malloc/free mock with fixed block pool and log fragmentation stats.",
                                "estimated_hours": 4.5,
                                "ai_prompt": "Review a simple free-list allocator implementation for race conditions.",
                                "status": "planned",
                            },
                            {
                                "title": "Run Valgrind on Week 5 exercises",
                                "description": "Capture leak reports and add remediation notes.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Interpret Valgrind leak summary and suggest fixes for invalid reads.",
                                "status": "planned",
                            },
                            {
                                "title": "Write C macros cheat sheet",
                                "description": "Document safe macro patterns for register access.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Draft macros for bit-banding an STM32 peripheral register.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Valgrind Quick Start",
                                "type": "article",
                                "url": "https://valgrind.org/docs/manual/quick-start.html",
                                "notes": "Reference leak check commands.",
                            },
                            {
                                "title": "Embedded C Programming - Memory Chapter",
                                "type": "book",
                                "notes": "Revisit pointer safety guidelines.",
                            },
                        ],
                    },
                    {
                        "number": 7,
                        "start_date": "2025-12-07",
                        "end_date": "2025-12-13",
                        "focus": "Bit manipulation and ISR patterns",
                        "tasks": [
                            {
                                "title": "Complete HackerRank bit manipulation set",
                                "description": "Solve 10 problems and document optimized solutions.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Generate unit tests to validate bitmask helper functions.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement ISR-safe ring buffer",
                                "description": "Write circular buffer with volatile guards and test on QEMU.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Audit ring buffer code for data races between ISR and main loop.",
                                "status": "planned",
                            },
                            {
                                "title": "Document interrupt latency benchmarks",
                                "description": "Use QEMU timing to estimate response for simulated GPIO interrupt.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Summarize factors impacting interrupt latency on Cortex-M MCUs.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32CubeIDE Interrupt Tutorial",
                                "type": "course",
                                "url": "https://academy.st.com/interrupt-tutorial",
                                "notes": "Follow ISR configuration labs.",
                            },
                            {
                                "title": "Bit Hacks Guide",
                                "type": "article",
                                "url": "https://graphics.stanford.edu/~seander/bithacks.html",
                                "notes": "Bookmark for quick reference.",
                            },
                        ],
                    },
                    {
                        "number": 8,
                        "start_date": "2025-12-14",
                        "end_date": "2025-12-20",
                        "focus": "UART fundamentals and sprint showcase",
                        "tasks": [
                            {
                                "title": "Bit-banged UART prototype",
                                "description": "Implement transmit-only UART on STM32 GPIO and log waveform.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Advise on timing tolerances for software UART at 9600 baud.",
                                "status": "planned",
                            },
                            {
                                "title": "Record Phase 1 recap video",
                                "description": "Publish 5-minute YouTube summary and embed in portfolio.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Draft video script outline highlighting key wins and blockers.",
                            },
                            {
                                "title": "Take ARM Embedded Essentials mock exam",
                                "description": "Score at least 80% and log topics needing revision.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Create a study plan for remaining ARM Embedded Essentials modules.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "ARM Embedded Essentials Course",
                                "type": "course",
                                "url": "https://learn.arm.com/path/embedded-essentials",
                                "notes": "Complete modules 6-8.",
                            },
                            {
                                "title": "UART Timing Spreadsheet",
                                "type": "tool",
                                "notes": "Use Excel sheet to validate software UART timings.",
                            },
                        ],
                    },
                ],
                "projects": [
                    {
                        "name": "Voltage Divider CLI",
                        "description": "Python CLI utility for computing divider outputs and exporting CSV logs.",
                        "status": "in_progress",
                        "repo_url": "https://github.com/embedded-mastery-khashyap/voltage-divider-cli",
                        "due_date": "2025-11-10",
                    },
                    {
                        "name": "Bit-Banged UART Demo",
                        "description": "STM32 project showcasing software-based UART and waveform capture.",
                        "status": "planned",
                        "due_date": "2025-12-20",
                    },
                ],
                "certifications": [
                    {
                        "name": "ARM Embedded Essentials",
                        "provider": "arm.com",
                        "status": "in_progress",
                        "due_date": "2025-12-20",
                        "progress": 0.4,
                    }
                ],
                "metrics": [
                    {
                        "metric_type": "hours_target",
                        "value": 15,
                        "unit": "hours/week",
                        "recorded_date": "2025-10-26",
                    },
                    {
                        "metric_type": "projects_completed",
                        "value": 1,
                        "unit": "count",
                        "recorded_date": "2025-12-21",
                    },
                ],
            },
            {
                "name": "Phase 2: MCU Domination & Peripherals",
                "description": "Intensive MCU programming, peripheral mastery, and debugging tooling.",
                "start_date": "2026-01-05",
                "end_date": "2026-03-01",
                "weeks": [
                    {
                        "number": 9,
                        "start_date": "2026-01-05",
                        "end_date": "2026-01-11",
                        "focus": "AVR + ARM toolchains and bootloaders",
                        "tasks": [
                            {
                                "title": "Set up PlatformIO projects for UNO and STM32",
                                "description": "Verify serial upload and printf diagnostics on both boards.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Generate PlatformIO configuration for STM32 Nucleo F401 board with FreeRTOS option.",
                                "status": "planned",
                            },
                            {
                                "title": "Study STM32 Step-by-Step modules 1-5",
                                "description": "Complete LED blink, button input, and timer labs.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Summarize the STM32 boot process from reset vector to main() entry.",
                                "status": "planned",
                            },
                            {
                                "title": "Flash custom bootloader example",
                                "description": "Build MCUBoot sample and document flashing workflow.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Explain the difference between a stage-1 and stage-2 bootloader for Cortex-M.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32 Step-by-Step Guide",
                                "type": "course",
                                "url": "https://www.st.com/en/support/learning/stm32-education.html",
                                "notes": "Finish fundamentals track.",
                            },
                            {
                                "title": "AVR Bootloader Application Note",
                                "type": "article",
                                "url": "https://www.microchip.com/en-us/application-notes/an1310",
                                "notes": "Review fuse settings cheat-sheet.",
                            },
                        ],
                    },
                    {
                        "number": 10,
                        "start_date": "2026-01-12",
                        "end_date": "2026-01-18",
                        "focus": "PWM motor controller sprint",
                        "tasks": [
                            {
                                "title": "Implement PWM motor driver on STM32",
                                "description": "Use HAL timers to drive motor shield at multiple duty cycles.",
                                "estimated_hours": 4.5,
                                "ai_prompt": "Tune PWM frequency for DC motor torque stability at 12V supply.",
                                "status": "planned",
                            },
                            {
                                "title": "Measure current draw + thermal profile",
                                "description": "Capture bench measurements and plot using pandas.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Write Python script to plot PWM duty vs current using seaborn.",
                                "status": "planned",
                            },
                            {
                                "title": "Document closed-loop considerations",
                                "description": "Outline how to add PID feedback in future iteration.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Summarize sensor options for closed-loop motor speed control.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32 PWM Cookbook",
                                "type": "article",
                                "url": "https://www.st.com/resource/en/application_note/dm00231426.pdf",
                                "notes": "Reference timer configuration.",
                            },
                            {
                                "title": "pandas Visualization Guide",
                                "type": "article",
                                "url": "https://pandas.pydata.org/docs/user_guide/visualization.html",
                                "notes": "Plot duty cycle vs current curve.",
                            },
                        ],
                    },
                    {
                        "number": 11,
                        "start_date": "2026-01-19",
                        "end_date": "2026-01-25",
                        "focus": "GPIO, timers, and debouncing patterns",
                        "tasks": [
                            {
                                "title": "Implement interrupt-driven button handler",
                                "description": "Use EXTI lines and software debounce with timer callbacks.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Provide pseudocode for dual-stage debouncing using timer capture compare.",
                                "status": "planned",
                            },
                            {
                                "title": "Toggle LED patterns using hardware timers",
                                "description": "Configure STM32 TIM3 to run LED multiplexer.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Explain effect of prescaler changes on timer tick resolution.",
                                "status": "planned",
                            },
                            {
                                "title": "Produce GPIO benchmarking report",
                                "description": "Measure interrupt latency vs polling for button inputs.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Interpret scope captures comparing ISR and polling response time.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32 Timer Overview",
                                "type": "article",
                                "url": "https://community.st.com/s/article/timer-overview",
                                "notes": "Bookmark for later DMA usage.",
                            },
                            {
                                "title": "Bounce2 Arduino Library",
                                "type": "tool",
                                "url": "https://github.com/thomasfredericks/Bounce2",
                                "notes": "Study design choices for debouncing.",
                            },
                        ],
                    },
                    {
                        "number": 12,
                        "start_date": "2026-01-26",
                        "end_date": "2026-02-01",
                        "focus": "I2C sensor hub baseline",
                        "tasks": [
                            {
                                "title": "Integrate three I2C sensors on ESP32",
                                "description": "Read IMU, temperature, and light sensor, log to serial.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Troubleshoot I2C bus lockups when mixing 5V and 3.3V peripherals.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement sensor abstraction layer",
                                "description": "Create interface for plug-and-play sensor modules.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Generate C++ header for polymorphic sensor driver manager.",
                                "status": "planned",
                            },
                            {
                                "title": "Profile bus bandwidth",
                                "description": "Measure average I2C throughput and document bottlenecks.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Advise on optimizing I2C pull-up resistor selection for 400kHz.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "ESP32 Technical Reference",
                                "type": "book",
                                "url": "https://www.espressif.com/sites/default/files/documentation/esp32_technical_reference_manual_en.pdf",
                                "notes": "Consult I2C peripheral section.",
                            },
                            {
                                "title": "Logic Analyzer Handbook",
                                "type": "article",
                                "notes": "Use LA to verify signal integrity.",
                            },
                        ],
                    },
                    {
                        "number": 13,
                        "start_date": "2026-02-02",
                        "end_date": "2026-02-08",
                        "focus": "UART and SPI protocol mastery",
                        "tasks": [
                            {
                                "title": "Create shared UART logging module",
                                "description": "Design thread-safe logging utility for STM32 and ESP32 projects.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Refactor UART driver to support DMA double buffering for high throughput.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement SPI display driver",
                                "description": "Drive 128x64 OLED with DMA transfers and frame buffer.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Outline SPI initialization sequence for SSD1306 display with DMA.",
                                "status": "planned",
                            },
                            {
                                "title": "Add protocol diagnostics",
                                "description": "Use minicom and logic analyzer to capture bus frames.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Provide checklist for debugging corrupted SPI transfers at 10MHz.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "minicom Serial Guide",
                                "type": "article",
                                "url": "https://wiki.archlinux.org/title/Minicom",
                                "notes": "Set up logging profiles.",
                            },
                            {
                                "title": "SPI Display Driver Example",
                                "type": "article",
                                "url": "https://learn.adafruit.com/monochrome-oled-breakouts/arduino-library-and-plays",
                                "notes": "Reference command sequences.",
                            },
                        ],
                    },
                    {
                        "number": 14,
                        "start_date": "2026-02-09",
                        "end_date": "2026-02-15",
                        "focus": "DMA throughput and debugging workflow",
                        "tasks": [
                            {
                                "title": "Configure DMA for SPI and ADC streams",
                                "description": "Implement double-buffered transfers and validate throughput.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Explain how DMA priority settings affect latency for competing peripherals.",
                                "status": "planned",
                            },
                            {
                                "title": "Debug I2C collision scenario",
                                "description": "Simulate multi-master bus in QEMU and resolve arbitration loss.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Generate test cases for multi-master I2C arbitration handling.",
                                "status": "planned",
                            },
                            {
                                "title": "Create peripheral troubleshooting checklist",
                                "description": "Document step-by-step process for UART/SPI/I2C failures.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Compose flowchart for narrowing down embedded peripheral faults.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32 DMA Application Note",
                                "type": "article",
                                "url": "https://www.st.com/resource/en/application_note/dm00046011.pdf",
                                "notes": "Review DMA configuration patterns.",
                            },
                            {
                                "title": "QEMU STM32 Lab",
                                "type": "tool",
                                "notes": "Use to emulate DMA transfers safely.",
                            },
                        ],
                    },
                    {
                        "number": 15,
                        "start_date": "2026-02-16",
                        "end_date": "2026-02-22",
                        "focus": "ADC audio sampler build",
                        "tasks": [
                            {
                                "title": "Sample microphone input via ADC",
                                "description": "Capture audio frames at 8kHz and store to SD card.",
                                "estimated_hours": 4.5,
                                "ai_prompt": "Suggest anti-aliasing filter design for 8kHz audio sampling on STM32.",
                                "status": "planned",
                            },
                            {
                                "title": "Run FFT analysis on captured data",
                                "description": "Use NumPy to plot frequency spectrum and highlight noise floor.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Provide Python snippet to compute FFT and annotate dominant frequencies.",
                                "status": "planned",
                            },
                            {
                                "title": "Write blog post about ADC project",
                                "description": "Publish Medium article with schematics and results.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Draft introduction describing why DMA is critical for audio capture.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "ADC Best Practices",
                                "type": "article",
                                "url": "https://www.analog.com/media/en/training-seminars/tutorials/MT-031.pdf",
                                "notes": "Review analog front-end guidelines.",
                            },
                            {
                                "title": "NumPy FFT Tutorial",
                                "type": "article",
                                "url": "https://numpy.org/doc/stable/reference/routines.fft.html",
                                "notes": "Reference FFT API usage.",
                            },
                        ],
                    },
                    {
                        "number": 16,
                        "start_date": "2026-02-23",
                        "end_date": "2026-03-01",
                        "focus": "Phase consolidation and deliverables",
                        "tasks": [
                            {
                                "title": "Create Phase 2 demo reel",
                                "description": "Record demos of PWM, I2C hub, ADC sampler and upload to YouTube playlist.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Write narration script highlighting technical depth for recruiters.",
                                "status": "planned",
                            },
                            {
                                "title": "Update documentation and READMEs",
                                "description": "Ensure each project repo has setup instructions and wiring diagrams.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Provide README template featuring build status, wiring tables, and demo links.",
                                "status": "planned",
                            },
                            {
                                "title": "Sit Emertxe embedded certification entrance test",
                                "description": "Complete mock exam and register for program.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Prepare a revision checklist for Emertxe entrance syllabus.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "YouTube Editing Workflow",
                                "type": "article",
                                "notes": "Set up DaVinci Resolve template.",
                            },
                            {
                                "title": "Emertxe Application Guide",
                                "type": "article",
                                "url": "https://www.emertxe.com/courses/advanced-embedded-systems-course/",
                                "notes": "Check latest exam dates.",
                            },
                        ],
                    },
                ],
                "projects": [
                    {
                        "name": "PWM Motor Controller",
                        "description": "STM32 HAL-based PWM driver with analytics and documentation.",
                        "status": "in_progress",
                        "repo_url": "https://github.com/embedded-mastery-khashyap/pwm-motor-controller",
                        "due_date": "2026-01-18",
                    },
                    {
                        "name": "I2C Sensor Hub",
                        "description": "ESP32 multi-sensor platform with abstraction layer and CSV logging.",
                        "status": "planned",
                        "due_date": "2026-02-10",
                    },
                    {
                        "name": "ADC Audio Sampler",
                        "description": "STM32 audio capture pipeline with FFT visualization notebook.",
                        "status": "planned",
                        "due_date": "2026-02-22",
                    },
                ],
                "certifications": [
                    {
                        "name": "Emertxe Embedded Certification",
                        "provider": "Emertxe",
                        "status": "in_progress",
                        "due_date": "2026-02-28",
                        "progress": 0.3,
                    }
                ],
                "metrics": [
                    {
                        "metric_type": "peripheral_quiz_score",
                        "value": 80,
                        "unit": "percent",
                        "recorded_date": "2026-02-01",
                    },
                    {
                        "metric_type": "hardware_hours_logged",
                        "value": 36,
                        "unit": "hours",
                        "recorded_date": "2026-02-23",
                    },
                ],
            },
            {
                "name": "Phase 3: RTOS & System Integration",
                "description": "Real-time scheduling, inter-process communication, and system integration.",
                "start_date": "2026-03-02",
                "end_date": "2026-04-26",
                "weeks": [
                    {
                        "number": 17,
                        "start_date": "2026-03-02",
                        "end_date": "2026-03-08",
                        "focus": "FreeRTOS fundamentals",
                        "tasks": [
                            {
                                "title": "Port FreeRTOS to STM32 demo app",
                                "description": "Create LED blinker with two concurrent tasks and measure jitter.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Explain scheduler tick configuration impacts on low-power modes.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement task communication via queues",
                                "description": "Demonstrate producer/consumer example with UART logging.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Review queue send/receive usage for ISR context in FreeRTOS.",
                                "status": "planned",
                            },
                            {
                                "title": "Write RTOS glossary",
                                "description": "Document definitions for tickless idle, priority inversion, and context switching.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Provide analogies for explaining priority inversion to interviewers.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "FreeRTOS Developer Guide",
                                "type": "book",
                                "url": "https://www.freertos.org/Documentation/161204_Mastering_the_FreeRTOS_Real_Time_Kernel-A_Hands-On_Tutorial_Guide.pdf",
                            },
                            {
                                "title": "STM32 FreeRTOS Workshop",
                                "type": "course",
                                "notes": "Complete labs 1-3.",
                            },
                        ],
                    },
                    {
                        "number": 18,
                        "start_date": "2026-03-09",
                        "end_date": "2026-03-15",
                        "focus": "Synchronization primitives",
                        "tasks": [
                            {
                                "title": "Implement mutex-protected shared buffer",
                                "description": "Use FreeRTOS mutex to guard sensor data structure.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Assess when to prefer mutex vs semaphore in FreeRTOS.",
                                "status": "planned",
                            },
                            {
                                "title": "Investigate priority inversion scenario",
                                "description": "Simulate high/low priority task conflict and enable priority inheritance.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Design test harness to reproduce priority inversion with tracing.",
                                "status": "planned",
                            },
                            {
                                "title": "Deploy FreeRTOS+Trace",
                                "description": "Capture scheduling trace and annotate key events.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Explain how to interpret FreeRTOS trace timeline for CPU usage analysis.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Percepio Tracealyzer",
                                "type": "tool",
                                "url": "https://percepio.com/tracealyzer/",
                                "notes": "Use to visualize scheduling activity.",
                            },
                            {
                                "title": "FreeRTOS Synchronization Reference",
                                "type": "article",
                                "url": "https://www.freertos.org/Embedded-RTOS-Co-routines.html",
                                "notes": "Review semaphores vs mutex guidance.",
                            },
                        ],
                    },
                    {
                        "number": 19,
                        "start_date": "2026-03-16",
                        "end_date": "2026-03-22",
                        "focus": "Interrupt safety and deferred processing",
                        "tasks": [
                            {
                                "title": "Implement ISR-to-task deferred work pattern",
                                "description": "Use stream buffers to offload heavy processing from ISR context.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Show best practices for minimizing ISR duration in FreeRTOS projects.",
                                "status": "planned",
                            },
                            {
                                "title": "Benchmark interrupt latency",
                                "description": "Measure latency with and without critical sections using logic analyzer.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Explain trade-offs between masking interrupts vs using priority levels.",
                                "status": "planned",
                            },
                            {
                                "title": "Document ISR design checklist",
                                "description": "Create checklist for stack usage, shared data access, and reentrancy.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Draft ISR audit checklist for code reviews.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "FreeRTOS Interrupt Management",
                                "type": "article",
                                "url": "https://www.freertos.org/FAQHelp.html#InterruptPriority",
                                "notes": "Review interrupt priority requirements.",
                            },
                            {
                                "title": "Logic Analyzer Toolkit",
                                "type": "tool",
                                "notes": "Capture precise ISR timing measurements.",
                            },
                        ],
                    },
                    {
                        "number": 20,
                        "start_date": "2026-03-23",
                        "end_date": "2026-03-29",
                        "focus": "RTOS data logger integration",
                        "tasks": [
                            {
                                "title": "Build FreeRTOS data logger",
                                "description": "Log multi-sensor data to SD with queue-based transport.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Discuss SD card wear-leveling considerations for data loggers.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement CLI command shell",
                                "description": "Use FreeRTOS+CLI for runtime configuration of loggers.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Generate command handler for adjusting logging interval via CLI.",
                                "status": "planned",
                            },
                            {
                                "title": "Plot logged data in Python",
                                "description": "Create pandas analysis notebook with charts and anomaly detection.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Write pandas script to detect sensor outliers using rolling average.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "FreeRTOS+CLI Reference",
                                "type": "article",
                                "url": "https://www.freertos.org/FreeRTOS-Plus/FreeRTOS_Plus_CLI/index.html",
                                "notes": "Implement command handlers.",
                            },
                            {
                                "title": "pandas Time-Series Guide",
                                "type": "article",
                                "url": "https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html",
                                "notes": "Analyze logged sensor data.",
                            },
                        ],
                    },
                    {
                        "number": 21,
                        "start_date": "2026-03-30",
                        "end_date": "2026-04-05",
                        "focus": "Power management strategies",
                        "tasks": [
                            {
                                "title": "Implement tickless idle mode",
                                "description": "Measure power savings on STM32 with FreeRTOS tickless configuration.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Outline steps to enable tickless idle on Cortex-M using LPTIM.",
                                "status": "planned",
                            },
                            {
                                "title": "Profile energy consumption",
                                "description": "Use INA219 sensor to log current draw across sleep/wake cycles.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Generate Python script to compute mAh usage per day from INA219 logs.",
                                "status": "planned",
                            },
                            {
                                "title": "Evaluate power-state transition logic",
                                "description": "Document state diagram for sleep/wake sequencing.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Create state diagram for power-driven RTOS scheduler.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Low Power Design for FreeRTOS",
                                "type": "article",
                                "url": "https://www.freertos.org/low-power-tickless-Idle.html",
                                "notes": "Follow configuration example.",
                            },
                            {
                                "title": "INA219 Current Sensor Datasheet",
                                "type": "book",
                                "url": "https://www.ti.com/lit/ds/symlink/ina219.pdf",
                                "notes": "Review accuracy guidelines.",
                            },
                        ],
                    },
                    {
                        "number": 22,
                        "start_date": "2026-04-06",
                        "end_date": "2026-04-12",
                        "focus": "Fault tolerance and watchdog design",
                        "tasks": [
                            {
                                "title": "Integrate hardware watchdog",
                                "description": "Configure independent watchdog and feed strategy within FreeRTOS tasks.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Explain when to use hardware vs software watchdogs in embedded systems.",
                                "status": "planned",
                            },
                            {
                                "title": "Simulate task failure scenarios",
                                "description": "Use fault injection to test watchdog response and recovery procedures.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Design test plan for validating watchdog reset paths.",
                                "status": "planned",
                            },
                            {
                                "title": "Plan maintenance hooks",
                                "description": "Document runtime self-test hooks and logging escalation.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Draft failure escalation matrix for embedded data logger.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32 Watchdog Application Note",
                                "type": "article",
                                "url": "https://www.st.com/resource/en/application_note/cd00296952.pdf",
                                "notes": "Follow best practices for IWDG.",
                            },
                            {
                                "title": "Fault Injection Strategies",
                                "type": "article",
                                "notes": "Compile list of failure modes to test.",
                            },
                        ],
                    },
                    {
                        "number": 23,
                        "start_date": "2026-04-13",
                        "end_date": "2026-04-19",
                        "focus": "Testing automation and CI groundwork",
                        "tasks": [
                            {
                                "title": "Set up Unity + CMock tests",
                                "description": "Write unit tests for peripheral drivers with hardware abstraction.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Generate sample Unity test for GPIO toggle function.",
                                "status": "planned",
                            },
                            {
                                "title": "Configure GitHub Actions for firmware",
                                "description": "Automate build, static analysis, and unit test stages.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Draft GitHub Actions workflow for PlatformIO project with cache.",
                                "status": "planned",
                            },
                            {
                                "title": "Run coverage analysis",
                                "description": "Use gcov to measure code coverage and set baseline targets.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Explain how to interpret gcov output for embedded C projects.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Unity Test Framework",
                                "type": "tool",
                                "url": "https://github.com/ThrowTheSwitch/Unity",
                                "notes": "Set up with CMock integration.",
                            },
                            {
                                "title": "GitHub Actions for Embedded",
                                "type": "article",
                                "url": "https://embeddedartistry.com/blog/2020/02/24/using-github-actions-with-embedded-projects/",
                                "notes": "Reference CI templates.",
                            },
                        ],
                    },
                    {
                        "number": 24,
                        "start_date": "2026-04-20",
                        "end_date": "2026-04-26",
                        "focus": "Phase integration and showcase",
                        "tasks": [
                            {
                                "title": "Record RTOS integration demo",
                                "description": "Capture video walkthrough of data logger, power management, and tracing tools.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Write narration script emphasizing system-level integration skills.",
                                "status": "planned",
                            },
                            {
                                "title": "Publish case study blog",
                                "description": "Detail architecture decisions, challenges, and metrics.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Draft case study outline for RTOS-enabled data logger.",
                                "status": "planned",
                            },
                            {
                                "title": "Update portfolio and resume",
                                "description": "Add RTOS accomplishments and metrics to portfolio site.",
                                "estimated_hours": 1.0,
                                "ai_prompt": "Suggest bullet points showcasing FreeRTOS expertise for resume.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "DaVinci Resolve Editing Template",
                                "type": "tool",
                                "notes": "Reuse for technical demo videos.",
                            },
                            {
                                "title": "Technical Blog Checklist",
                                "type": "article",
                                "notes": "Ensure case study covers goals, architecture, results.",
                            },
                        ],
                    },
                ],
                "projects": [
                    {
                        "name": "FreeRTOS Task Manager",
                        "description": "Multitask demo with scheduling trace and documentation.",
                        "status": "planned",
                        "due_date": "2026-03-15",
                    },
                    {
                        "name": "RTOS Data Logger",
                        "description": "Queue-based sensor logging platform with CLI control.",
                        "status": "planned",
                        "due_date": "2026-03-29",
                    },
                    {
                        "name": "Power-Optimized Logger",
                        "description": "Tickless FreeRTOS build with energy profiling and report.",
                        "status": "planned",
                        "due_date": "2026-04-12",
                    },
                ],
                "certifications": [
                    {
                        "name": "IIT Kanpur Embedded Systems",
                        "provider": "IIT Kanpur",
                        "status": "planned",
                        "due_date": "2026-04-30",
                        "progress": 0.2,
                    }
                ],
                "metrics": [
                    {
                        "metric_type": "rtos_trace_sessions",
                        "value": 6,
                        "unit": "sessions",
                        "recorded_date": "2026-04-01",
                    },
                    {
                        "metric_type": "blog_posts_published",
                        "value": 1,
                        "unit": "count",
                        "recorded_date": "2026-04-25",
                    },
                ],
            },
            {
                "name": "Phase 4: Advanced Optimization & Edge Cases",
                "description": "Security, advanced RTOS, edge AI, and RISC-V exploration.",
                "start_date": "2026-05-04",
                "end_date": "2026-07-26",
                "weeks": [
                    {
                        "number": 25,
                        "start_date": "2026-05-04",
                        "end_date": "2026-05-10",
                        "focus": "Advanced RTOS scheduling and SMP concepts",
                        "tasks": [
                            {
                                "title": "Study FreeRTOS SMP design notes",
                                "description": "Summarize scheduling differences and portability considerations.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Compare SMP-enabled FreeRTOS with Zephyr multicore scheduling.",
                                "status": "planned",
                            },
                            {
                                "title": "Prototype load monitoring task",
                                "description": "Implement CPU load monitor with runtime stats collection.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Generate FreeRTOS config macros for runtime stats instrumentation.",
                                "status": "planned",
                            },
                            {
                                "title": "Review advanced semaphore patterns",
                                "description": "Document barriers, counting semaphores, and event groups use cases.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Provide decision matrix for choosing FreeRTOS synchronization primitive.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "FreeRTOS SMP Whitepaper",
                                "type": "article",
                                "notes": "Gather design insights for multicore scheduling.",
                            },
                            {
                                "title": "Event Groups Tutorial",
                                "type": "article",
                                "url": "https://www.freertos.org/FreeRTOS-Event-Groups.html",
                                "notes": "Review event group API.",
                            },
                        ],
                    },
                    {
                        "number": 26,
                        "start_date": "2026-05-11",
                        "end_date": "2026-05-17",
                        "focus": "Low-level device driver deep dive",
                        "tasks": [
                            {
                                "title": "Write bare-metal I2S driver",
                                "description": "Implement register-level driver for audio streaming.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Suggest register configuration sequence for STM32 I2S full duplex.",
                                "status": "planned",
                            },
                            {
                                "title": "Create unit tests for driver",
                                "description": "Use Unity with hardware abstraction to verify driver logic.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Generate stub interfaces for mocking STM32 I2S registers.",
                                "status": "planned",
                            },
                            {
                                "title": "Document driver porting guide",
                                "description": "Write README covering assumptions, integration steps, and limitations.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Provide documentation outline for reusable embedded driver module.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32 I2S Application Note",
                                "type": "article",
                                "url": "https://www.st.com/resource/en/application_note/dm00189125.pdf",
                                "notes": "Follow initialization flowcharts.",
                            },
                            {
                                "title": "Unity Mocking Guide",
                                "type": "article",
                                "url": "https://github.com/ThrowTheSwitch/CMock",
                                "notes": "Set up CMock for register mocking.",
                            },
                        ],
                    },
                    {
                        "number": 27,
                        "start_date": "2026-05-18",
                        "end_date": "2026-05-24",
                        "focus": "Security foundations for embedded systems",
                        "tasks": [
                            {
                                "title": "Research secure boot chain",
                                "description": "Map key provisioning, signing, and boot verification flow.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Summarize secure boot threat model for consumer IoT device.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement AES encryption demo",
                                "description": "Use hardware crypto peripheral to encrypt sensor payloads.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Write C function to wrap STM32 AES peripheral for 128-bit CBC mode.",
                                "status": "planned",
                            },
                            {
                                "title": "Document key management strategy",
                                "description": "Define approach for storing secrets and rotating keys.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Create checklist for managing cryptographic material on MCUs.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "STM32 Security Primer",
                                "type": "article",
                                "url": "https://www.st.com/resource/en/application_note/dm00203147.pdf",
                                "notes": "Study secure boot and crypto sections.",
                            },
                            {
                                "title": "ARM PSA Security Model",
                                "type": "article",
                                "url": "https://www.arm.com/architecture/security-features/platform-security",
                                "notes": "Understand PSA Certified requirements.",
                            },
                        ],
                    },
                    {
                        "number": 28,
                        "start_date": "2026-05-25",
                        "end_date": "2026-05-31",
                        "focus": "Secure IoT gateway project",
                        "tasks": [
                            {
                                "title": "Integrate TLS stack on STM32",
                                "description": "Set up mbedTLS HTTPS client with certificate validation.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Outline steps to enable hardware acceleration for mbedTLS on STM32.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement secure firmware update flow",
                                "description": "Simulate OTA update with signature verification and rollback.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Design state machine for secure OTA update with fail-safe rollback.",
                                "status": "planned",
                            },
                            {
                                "title": "Capture Wireshark traces",
                                "description": "Verify encrypted communication and document handshake details.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "List Wireshark filters to validate TLS handshake certificates.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "mbedTLS Documentation",
                                "type": "article",
                                "url": "https://tls.mbed.org/api/",
                                "notes": "Review client setup examples.",
                            },
                            {
                                "title": "Wireshark TLS Analysis Guide",
                                "type": "article",
                                "notes": "Ensure capture validates cipher suite selection.",
                            },
                        ],
                    },
                    {
                        "number": 29,
                        "start_date": "2026-06-01",
                        "end_date": "2026-06-07",
                        "focus": "TinyML onboarding",
                        "tasks": [
                            {
                                "title": "Complete TinyML Coursera Week 1",
                                "description": "Understand ML pipeline for microcontrollers.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Summarize differences between TensorFlow Lite and TFLite Micro.",
                                "status": "planned",
                            },
                            {
                                "title": "Set up TensorFlow Lite toolchain",
                                "description": "Install dependencies and verify sample inference on desktop.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Provide Dockerfile for TensorFlow Lite Micro build environment.",
                                "status": "planned",
                            },
                            {
                                "title": "Collect dataset for gesture classification",
                                "description": "Record accelerometer data for 3 gestures and label in Notion.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Suggest data augmentation techniques for IMU gesture dataset.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "TinyML Course",
                                "type": "course",
                                "url": "https://www.coursera.org/learn/tinyml",
                                "notes": "Complete lessons and labs.",
                            },
                            {
                                "title": "TensorFlow Lite Micro Guide",
                                "type": "article",
                                "url": "https://www.tensorflow.org/lite/microcontrollers",
                                "notes": "Review microcontroller build setup.",
                            },
                        ],
                    },
                    {
                        "number": 30,
                        "start_date": "2026-06-08",
                        "end_date": "2026-06-14",
                        "focus": "Real-time audio processor",
                        "tasks": [
                            {
                                "title": "Design audio DSP pipeline",
                                "description": "Implement FIR filter and gain control on STM32.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Provide CMSIS-DSP function selections for 8kHz audio pipeline.",
                                "status": "planned",
                            },
                            {
                                "title": "Run ML inference on audio features",
                                "description": "Deploy keyword spotting model and measure latency.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Explain how to quantize keyword spotting model for STM32.",
                                "status": "planned",
                            },
                            {
                                "title": "Benchmark CPU and memory usage",
                                "description": "Profile pipeline performance and document headroom.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Generate profiling checklist for DSP + ML workloads on MCUs.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "CMSIS-DSP Library",
                                "type": "tool",
                                "url": "https://arm-software.github.io/CMSIS_5/DSP/html/index.html",
                                "notes": "Reference audio processing functions.",
                            },
                            {
                                "title": "Keyword Spotting Example",
                                "type": "article",
                                "url": "https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite/micro/examples/micro_speech",
                                "notes": "Use as baseline model.",
                            },
                        ],
                    },
                    {
                        "number": 31,
                        "start_date": "2026-06-15",
                        "end_date": "2026-06-21",
                        "focus": "Model optimization and deployment",
                        "tasks": [
                            {
                                "title": "Perform model quantization",
                                "description": "Convert model to int8 and validate accuracy on test set.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Explain post-training quantization workflow for TFLite Micro.",
                                "status": "planned",
                            },
                            {
                                "title": "Integrate model with C++ inference engine",
                                "description": "Embed TFLite Micro runtime into STM32 project.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Provide code snippet to initialize TFLite Micro interpreter on Cortex-M.",
                                "status": "planned",
                            },
                            {
                                "title": "Develop on-device telemetry",
                                "description": "Log inference confidence and send to PC dashboard.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Design UART protocol for streaming inference metrics to Python dashboard.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "TensorFlow Lite Micro Interpreter",
                                "type": "article",
                                "url": "https://www.tensorflow.org/lite/microcontrollers/build_convert",
                                "notes": "Check interpreter initialization steps.",
                            },
                            {
                                "title": "Edge ML Telemetry Dashboard",
                                "type": "article",
                                "notes": "Plan metrics capture format.",
                            },
                        ],
                    },
                    {
                        "number": 32,
                        "start_date": "2026-06-22",
                        "end_date": "2026-06-28",
                        "focus": "Embedded Linux bring-up",
                        "tasks": [
                            {
                                "title": "Build Yocto minimal image",
                                "description": "Create custom Linux image for ARM board and boot QEMU.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Outline Yocto layers required for minimal embedded Linux image.",
                                "status": "planned",
                            },
                            {
                                "title": "Develop user-space driver",
                                "description": "Write Python script interacting with GPIO via sysfs.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Provide Python example toggling GPIO on embedded Linux using sysfs.",
                                "status": "planned",
                            },
                            {
                                "title": "Document BSP customization",
                                "description": "Capture steps for adding custom kernel module.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Draft checklist for porting Linux BSP to new embedded board.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Yocto Project Quick Start",
                                "type": "article",
                                "url": "https://docs.yoctoproject.org/brief-yoctoprojectqs/index.html",
                                "notes": "Follow minimal image build.",
                            },
                            {
                                "title": "Embedded Linux GPIO Tutorial",
                                "type": "article",
                                "notes": "Review sysfs access patterns.",
                            },
                        ],
                    },
                    {
                        "number": 33,
                        "start_date": "2026-06-29",
                        "end_date": "2026-07-05",
                        "focus": "RISC-V ISA study",
                        "tasks": [
                            {
                                "title": "Complete RISC-V online course module 1",
                                "description": "Understand base ISA, privilege levels, and toolchain setup.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Summarize differences between RV32I and RV64I instruction sets.",
                                "status": "planned",
                            },
                            {
                                "title": "Run Spike simulator",
                                "description": "Assemble simple programs and inspect pipeline behavior.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Provide Spike commands to step through RISC-V instructions.",
                                "status": "planned",
                            },
                            {
                                "title": "Document ISA flashcards",
                                "description": "Create Notion deck for key RISC-V instructions and usage.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Create spaced repetition prompts for RISC-V register usage.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "RISC-V Reader",
                                "type": "book",
                                "url": "https://github.com/riscv/documents/blob/master/riscv-spec-V2.2.pdf",
                                "notes": "Reference base spec sections.",
                            },
                            {
                                "title": "SiFive E-SDK",
                                "type": "tool",
                                "notes": "Prepare environment for hardware prototyping.",
                            },
                        ],
                    },
                    {
                        "number": 34,
                        "start_date": "2026-07-06",
                        "end_date": "2026-07-12",
                        "focus": "RISC-V bare metal project",
                        "tasks": [
                            {
                                "title": "Bring up RISC-V dev board",
                                "description": "Blink LED using assembly and C startup code.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Generate linker script skeleton for bare-metal RISC-V project.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement UART driver",
                                "description": "Write minimal UART driver and integrate with printf.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Provide register map for common RISC-V UART peripheral.",
                                "status": "planned",
                            },
                            {
                                "title": "Benchmark context switch",
                                "description": "Measure simple cooperative scheduler performance.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Explain how CSR instructions aid context switching on RISC-V.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "RISC-V Bare-Metal Tutorial",
                                "type": "article",
                                "notes": "Follow step-by-step bring-up guide.",
                            },
                            {
                                "title": "OpenOCD RISC-V Guide",
                                "type": "article",
                                "notes": "Configure debugger for board.",
                            },
                        ],
                    },
                    {
                        "number": 35,
                        "start_date": "2026-07-13",
                        "end_date": "2026-07-19",
                        "focus": "FPGA prototyping introduction",
                        "tasks": [
                            {
                                "title": "Install FPGA toolchain",
                                "description": "Set up open-source flow (Yosys/NextPNR) and run blink example.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "List steps for synthesizing Verilog design using Yosys.",
                                "status": "planned",
                            },
                            {
                                "title": "Design simple PWM in Verilog",
                                "description": "Implement PWM core and validate using simulation and board LEDs.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Generate testbench for Verilog PWM module.",
                                "status": "planned",
                            },
                            {
                                "title": "Document FPGA vs MCU tradeoffs",
                                "description": "Summarize use cases for moving workloads to FPGA.",
                                "estimated_hours": 1.0,
                                "ai_prompt": "Provide comparison table of MCU vs FPGA for embedded acceleration.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "FPGA Open-Source Tooling Guide",
                                "type": "article",
                                "url": "https://github.com/YosysHQ/fpga-toolchain",
                                "notes": "Follow installation instructions.",
                            },
                            {
                                "title": "Verilog Basics",
                                "type": "course",
                                "notes": "Review combinational and sequential constructs.",
                            },
                        ],
                    },
                    {
                        "number": 36,
                        "start_date": "2026-07-20",
                        "end_date": "2026-07-26",
                        "focus": "AI edge fusion showcase",
                        "tasks": [
                            {
                                "title": "Combine TinyML with secure gateway",
                                "description": "Send inference results via TLS gateway to cloud dashboard.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Design MQTT topic hierarchy for streaming inference metrics securely.",
                                "status": "planned",
                            },
                            {
                                "title": "Create demo video and GitHub README",
                                "description": "Highlight end-to-end data flow, security, and ML insights.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Write README section explaining hybrid edge AI architecture.",
                                "status": "planned",
                            },
                            {
                                "title": "Submit project to Hackster.io",
                                "description": "Publish article with build steps, code, and lessons learned.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Outline Hackster.io submission structure for edge AI project.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Hackster.io Submission Checklist",
                                "type": "article",
                                "notes": "Ensure project meets judging criteria.",
                            },
                            {
                                "title": "MQTT Security Best Practices",
                                "type": "article",
                                "notes": "Validate secure messaging configuration.",
                            },
                        ],
                    },
                ],
                "projects": [
                    {
                        "name": "Secure IoT Gateway",
                        "description": "TLS-enabled STM32 gateway with OTA update pipeline.",
                        "status": "planned",
                        "due_date": "2026-05-31",
                    },
                    {
                        "name": "TinyML Gesture Classifier",
                        "description": "Edge ML model with telemetry dashboard and documentation.",
                        "status": "planned",
                        "due_date": "2026-06-21",
                    },
                    {
                        "name": "RISC-V Bare Metal Suite",
                        "description": "RISC-V firmware experiments covering UART, blink, and scheduler.",
                        "status": "planned",
                        "due_date": "2026-07-12",
                    },
                ],
                "certifications": [
                    {
                        "name": "FreeRTOS Advanced Certificate",
                        "provider": "FreeRTOS Academy",
                        "status": "planned",
                        "due_date": "2026-07-01",
                        "progress": 0.1,
                    }
                ],
                "metrics": [
                    {
                        "metric_type": "hackster_submission",
                        "value": 1,
                        "unit": "count",
                        "recorded_date": "2026-07-25",
                    },
                    {
                        "metric_type": "ml_inference_latency",
                        "value": 35,
                        "unit": "ms",
                        "recorded_date": "2026-06-18",
                    },
                ],
            },
            {
                "name": "Phase 5: Mastery, Portfolio & Job Conquest",
                "description": "Portfolio polish, interview preparation, and job acquisition.",
                "start_date": "2026-08-03",
                "end_date": "2026-10-25",
                "weeks": [
                    {
                        "number": 37,
                        "start_date": "2026-08-03",
                        "end_date": "2026-08-09",
                        "focus": "Knowledge consolidation",
                        "tasks": [
                            {
                                "title": "Run comprehensive knowledge audit",
                                "description": "List strengths/gaps across MCU, RTOS, security, ML.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Design rubric to score embedded competencies before interviews.",
                                "status": "planned",
                            },
                            {
                                "title": "Curate best projects",
                                "description": "Select top five builds to feature in portfolio landing page.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Suggest compelling narratives for top embedded projects.",
                                "status": "planned",
                            },
                            {
                                "title": "Plan content refresh",
                                "description": "Schedule updates for README, blog, and LinkedIn summary.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Generate LinkedIn headline variants emphasizing embedded mastery.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Portfolio Audit Template",
                                "type": "tool",
                                "notes": "Notion template for skills inventory.",
                            },
                            {
                                "title": "STAR Story Guide",
                                "type": "article",
                                "notes": "Prepare achievement stories.",
                            },
                        ],
                    },
                    {
                        "number": 38,
                        "start_date": "2026-08-10",
                        "end_date": "2026-08-16",
                        "focus": "Industry trends and research",
                        "tasks": [
                            {
                                "title": "Study 2026 embedded trend reports",
                                "description": "Summarize key takeaways from RISC-V, Edge AI, and security reports.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Highlight top 5 embedded trends to mention in interviews.",
                                "status": "planned",
                            },
                            {
                                "title": "Update competitive research",
                                "description": "List target companies and their tech focus areas.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Create comparison matrix for target employers and required skills.",
                                "status": "planned",
                            },
                            {
                                "title": "Draft future roadmap v1.2",
                                "description": "Plan mobile companion app and cloud backup features.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Outline roadmap for Flutter companion app integrating with tracker.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "RISC-V 2026 Outlook",
                                "type": "article",
                                "notes": "Capture growth segments to reference in interviews.",
                            },
                            {
                                "title": "Edge AI Market Report",
                                "type": "article",
                                "notes": "Note demand for ML on MCUs.",
                            },
                        ],
                    },
                    {
                        "number": 39,
                        "start_date": "2026-08-17",
                        "end_date": "2026-08-23",
                        "focus": "Community contributions",
                        "tasks": [
                            {
                                "title": "Publish open-source issue fixes",
                                "description": "Contribute patch to FreeRTOS or TinyML repository.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Draft pull request message outlining fix and tests.",
                                "status": "planned",
                            },
                            {
                                "title": "Host LinkedIn knowledge share",
                                "description": "Run live session summarizing lessons from Phase 4.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Generate outline for live session on secure edge ML.",
                                "status": "planned",
                            },
                            {
                                "title": "Engage in 3 community discussions",
                                "description": "Participate in r/embedded and ARM forums.",
                                "estimated_hours": 1.0,
                                "ai_prompt": "Suggest talking points for embedded forum discussions.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "FreeRTOS Contribution Guide",
                                "type": "article",
                                "notes": "Follow coding standards for PR.",
                            },
                            {
                                "title": "LinkedIn Live Checklist",
                                "type": "tool",
                                "notes": "Ensure session is structured and recorded.",
                            },
                        ],
                    },
                    {
                        "number": 40,
                        "start_date": "2026-08-24",
                        "end_date": "2026-08-30",
                        "focus": "RISC-V secure boot build",
                        "tasks": [
                            {
                                "title": "Implement secure boot prototype",
                                "description": "Add signature verification to RISC-V firmware loader.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Provide steps to integrate signature verification into RISC-V bootloader.",
                                "status": "planned",
                            },
                            {
                                "title": "Document threat model",
                                "description": "Identify attack vectors and mitigations for secure boot.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Generate threat model diagram for secure boot flow.",
                                "status": "planned",
                            },
                            {
                                "title": "Record demo video",
                                "description": "Show secure boot validation and failure handling.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Draft script explaining secure boot verification steps.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "RISC-V Secure Boot Guide",
                                "type": "article",
                                "notes": "Summarize recommended practices.",
                            },
                            {
                                "title": "Threat Modeling Toolkit",
                                "type": "tool",
                                "notes": "Use to diagram threats (STRIDE).",
                            },
                        ],
                    },
                    {
                        "number": 41,
                        "start_date": "2026-08-31",
                        "end_date": "2026-09-06",
                        "focus": "Portfolio refactor",
                        "tasks": [
                            {
                                "title": "Redesign portfolio site",
                                "description": "Update layout with timeline, case studies, and testimonials.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "List must-have sections for embedded engineering portfolio site.",
                                "status": "planned",
                            },
                            {
                                "title": "Create downloadable CV and case studies",
                                "description": "Produce PDF versions of resume and two project briefs.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Generate case study template for embedded project deliverables.",
                                "status": "planned",
                            },
                            {
                                "title": "Implement analytics tracking",
                                "description": "Add privacy-focused analytics to portfolio.",
                                "estimated_hours": 1.0,
                                "ai_prompt": "Recommend privacy-respecting analytics for personal site.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Portfolio Design Inspiration",
                                "type": "article",
                                "notes": "Collect layout ideas from top developers.",
                            },
                            {
                                "title": "Fathom Analytics Docs",
                                "type": "article",
                                "notes": "Implement privacy-first analytics.",
                            },
                        ],
                    },
                    {
                        "number": 42,
                        "start_date": "2026-09-07",
                        "end_date": "2026-09-13",
                        "focus": "Android-embedded integration",
                        "tasks": [
                            {
                                "title": "Develop Kotlin control app",
                                "description": "Build Android app to control ESP32 sensor hub via BLE.",
                                "estimated_hours": 4.0,
                                "ai_prompt": "Generate Kotlin BLE service code to connect to ESP32 characteristic.",
                                "status": "planned",
                            },
                            {
                                "title": "Sync roadmap tracker data",
                                "description": "Prototype mobile dashboard pulling data via REST API.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Design REST endpoints for mobile companion app to read tracker data.",
                                "status": "planned",
                            },
                            {
                                "title": "Record integration demo",
                                "description": "Show Android app toggling hardware features in real-time.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Outline storyboard for Android + embedded integration demo.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Android BLE Guide",
                                "type": "article",
                                "url": "https://developer.android.com/guide/topics/connectivity/bluetooth",
                                "notes": "Review BLE connection workflow.",
                            },
                            {
                                "title": "ESP32 BLE Examples",
                                "type": "article",
                                "notes": "Leverage sample code for characteristic updates.",
                            },
                        ],
                    },
                    {
                        "number": 43,
                        "start_date": "2026-09-14",
                        "end_date": "2026-09-20",
                        "focus": "GitHub automation and CI/CD",
                        "tasks": [
                            {
                                "title": "Build release pipeline",
                                "description": "Automate packaging of GUI/CLI releases via GitHub Actions.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Draft GitHub Actions workflow for PyInstaller builds on Linux and Windows.",
                                "status": "planned",
                            },
                            {
                                "title": "Integrate static analysis gates",
                                "description": "Add clang-tidy and cppcheck to firmware CI.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Provide Actions snippet to run cppcheck with warnings as errors.",
                                "status": "planned",
                            },
                            {
                                "title": "Automate project dashboards",
                                "description": "Use GitHub Projects automation for roadmap tracker milestones.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Explain how to auto-update GitHub Project fields using workflows.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "GitHub Actions Marketplace",
                                "type": "tool",
                                "notes": "Select reusable actions for builds.",
                            },
                            {
                                "title": "cppcheck Documentation",
                                "type": "article",
                                "notes": "Review recommended flags for embedded projects.",
                            },
                        ],
                    },
                    {
                        "number": 44,
                        "start_date": "2026-09-21",
                        "end_date": "2026-09-27",
                        "focus": "Marketing and demo polish",
                        "tasks": [
                            {
                                "title": "Produce flagship demo video",
                                "description": "Combine highlights from all phases into cohesive story.",
                                "estimated_hours": 3.5,
                                "ai_prompt": "Develop narrative arc for 5-minute embedded portfolio demo.",
                                "status": "planned",
                            },
                            {
                                "title": "Update GitHub README badges",
                                "description": "Add CI status, coverage, and download counts.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Generate markdown for dynamic badge integration.",
                                "status": "planned",
                            },
                            {
                                "title": "Prep email outreach list",
                                "description": "Collect contacts for targeted job outreach.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Draft professional outreach template for embedded roles.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Video Storytelling for Engineers",
                                "type": "article",
                                "notes": "Improve delivery in demo video.",
                            },
                            {
                                "title": "Email Outreach Template",
                                "type": "tool",
                                "notes": "Customize for target companies.",
                            },
                        ],
                    },
                    {
                        "number": 45,
                        "start_date": "2026-09-28",
                        "end_date": "2026-10-04",
                        "focus": "Interview preparation - technical",
                        "tasks": [
                            {
                                "title": "Solve embedded coding interview set",
                                "description": "Complete 20 targeted problems on arrays, pointers, and bit-twiddling.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Provide mock interview question set for embedded C pointers and ISR design.",
                                "status": "planned",
                            },
                            {
                                "title": "Review RTOS interview topics",
                                "description": "Create Q&A deck covering scheduling, synchronization, and debugging.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Generate 10 advanced RTOS interview questions with suggested answers.",
                                "status": "planned",
                            },
                            {
                                "title": "Conduct timed whiteboard drills",
                                "description": "Practice problem-solving under time constraints.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Outline daily practice routine for embedded whiteboard sessions.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Interview Cake Embedded Track",
                                "type": "course",
                                "notes": "Complete embedded-specific modules.",
                            },
                            {
                                "title": "FreeRTOS Interview Prep",
                                "type": "article",
                                "notes": "Compile key RTOS questions.",
                            },
                        ],
                    },
                    {
                        "number": 46,
                        "start_date": "2026-10-05",
                        "end_date": "2026-10-11",
                        "focus": "Mock interviews and feedback",
                        "tasks": [
                            {
                                "title": "Schedule mock interviews",
                                "description": "Book 3 mocks with peers/mentors focusing on systems design.",
                                "estimated_hours": 2.5,
                                "ai_prompt": "Prepare systems design prompt for mock interview sessions.",
                                "status": "planned",
                            },
                            {
                                "title": "Collect feedback and iterate",
                                "description": "Log improvements and plan targeted practice.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Create feedback tracker template for interview practice.",
                                "status": "planned",
                            },
                            {
                                "title": "Record self-review videos",
                                "description": "Analyze communication style and clarity.",
                                "estimated_hours": 1.0,
                                "ai_prompt": "List self-review questions for evaluating interview recordings.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Mock Interview Scheduler",
                                "type": "tool",
                                "notes": "Coordinate slots with mentors.",
                            },
                            {
                                "title": "Feedback Journal Template",
                                "type": "tool",
                                "notes": "Record insights after each mock.",
                            },
                        ],
                    },
                    {
                        "number": 47,
                        "start_date": "2026-10-12",
                        "end_date": "2026-10-18",
                        "focus": "Job applications pipeline",
                        "tasks": [
                            {
                                "title": "Launch 10 job applications",
                                "description": "Target Bosch, TI, Qualcomm, and top IoT startups.",
                                "estimated_hours": 3.0,
                                "ai_prompt": "Create Trello board template to track job application stages.",
                                "status": "planned",
                            },
                            {
                                "title": "Optimize resume per role",
                                "description": "Tailor bullet points to each application.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Generate ATS-friendly resume keywords for embedded roles.",
                                "status": "planned",
                            },
                            {
                                "title": "Engage referrals",
                                "description": "Reach out to LinkedIn connections for referrals.",
                                "estimated_hours": 1.0,
                                "ai_prompt": "Draft polite referral request message for alumni contacts.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Application Tracker Spreadsheet",
                                "type": "tool",
                                "notes": "Log status, contacts, and follow-up dates.",
                            },
                            {
                                "title": "Resume Tailoring Guide",
                                "type": "article",
                                "notes": "Ensure each resume variant is role-specific.",
                            },
                        ],
                    },
                    {
                        "number": 48,
                        "start_date": "2026-10-19",
                        "end_date": "2026-10-25",
                        "focus": "Offer readiness and retrospective",
                        "tasks": [
                            {
                                "title": "Prepare offer negotiation scripts",
                                "description": "Outline responses for compensation, benefits, and remote work discussions.",
                                "estimated_hours": 2.0,
                                "ai_prompt": "Draft salary negotiation script for ₹15-25 LPA target range.",
                                "status": "planned",
                            },
                            {
                                "title": "Conduct Phase 5 retrospective",
                                "description": "Document lessons, successes, and improvements for future cycles.",
                                "estimated_hours": 1.5,
                                "ai_prompt": "Provide retrospective template focusing on outcomes and next steps.",
                                "status": "planned",
                            },
                            {
                                "title": "Celebrate milestones",
                                "description": "Plan reward and share success with family/community.",
                                "estimated_hours": 1.0,
                                "ai_prompt": "Suggest celebration ideas aligned with long-term motivation.",
                                "status": "planned",
                            },
                        ],
                        "resources": [
                            {
                                "title": "Salary Negotiation Guide",
                                "type": "article",
                                "notes": "Leverage data-driven negotiation techniques.",
                            },
                            {
                                "title": "Retrospective Template",
                                "type": "tool",
                                "notes": "Capture wins, lessons, and next actions.",
                            },
                        ],
                    },
                ],
                "projects": [
                    {
                        "name": "Android + Embedded Companion",
                        "description": "Kotlin BLE app interfacing with ESP32 sensor hub and tracker backend.",
                        "status": "planned",
                        "due_date": "2026-09-13",
                    },
                    {
                        "name": "Portfolio Relaunch",
                        "description": "Revamped portfolio site with analytics, case studies, and CI-powered downloads.",
                        "status": "planned",
                        "due_date": "2026-09-06",
                    },
                    {
                        "name": "Interview Prep Toolkit",
                        "description": "Collection of scripts, Q&A decks, and automation for job search.",
                        "status": "planned",
                        "due_date": "2026-10-11",
                    },
                ],
                "certifications": [
                    {
                        "name": "ARM Certified Professional",
                        "provider": "arm.com",
                        "status": "planned",
                        "due_date": "2026-09-30",
                        "progress": 0.0,
                    }
                ],
                "metrics": [
                    {
                        "metric_type": "applications_submitted",
                        "value": 50,
                        "unit": "count",
                        "recorded_date": "2026-10-25",
                    },
                    {
                        "metric_type": "mock_interviews",
                        "value": 6,
                        "unit": "count",
                        "recorded_date": "2026-10-12",
                    },
                ],
            },
        ],
        "certifications": [
            {
                "name": "FreeRTOS Advanced Certificate",
                "provider": "FreeRTOS Academy",
                "status": "planned",
                "due_date": "2026-07-01",
                "progress": 0.1,
            },
            {
                "name": "ARM Certified Professional",
                "provider": "arm.com",
                "status": "planned",
                "due_date": "2026-09-30",
                "progress": 0.0,
            },
        ],
        "applications": [
            {
                "company": "Bosch India",
                "role": "Embedded Systems Engineer",
                "source": "LinkedIn",
                "status": "draft",
                "next_action": "Tailor resume with Phase 4 security accomplishments.",
            },
            {
                "company": "Texas Instruments",
                "role": "Embedded Firmware Developer",
                "source": "Referral",
                "status": "draft",
                "next_action": "Request referral after portfolio relaunch.",
            },
        ],
        "metrics": [
            {
                "metric_type": "hours_logged",
                "value": 10,
                "unit": "hours",
                "recorded_date": "2025-10-25",
            },
            {
                "metric_type": "github_followers",
                "value": 250,
                "unit": "count",
                "recorded_date": "2026-09-20",
            },
            {
                "metric_type": "linkedin_connections",
                "value": 600,
                "unit": "count",
                "recorded_date": "2026-10-01",
            },
        ],
    }
    _inject_daily_plan(seed)
    _harmonise_statuses(seed)
    return seed


def main() -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    seed_path = data_dir / "roadmap_seed.json"
    seed_path.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {seed_path}")


if __name__ == "__main__":
    main()
