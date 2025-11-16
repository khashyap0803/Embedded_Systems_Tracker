"""Generate a hyper-detailed 52-week embedded systems mastery roadmap seed."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List, Optional


START_DATE = date(2025, 10, 27)
MINUTES_PER_DAY = 240
MIN_SEGMENT_MINUTES = 45
INTEGRATION_MINUTES = 120
REVISION_PROMPT = (
    "Summarize takeaways, log blockers, and queue AI prompts for next sprint in Notion."
)


@dataclass(frozen=True)
class TaskPlan:
    title: str
    description: str
    estimated_hours: float
    ai_prompt: str
    status: str = "planned"


@dataclass(frozen=True)
class ResourcePlan:
    title: str
    type: str
    notes: str
    url: Optional[str] = None


@dataclass(frozen=True)
class WeekPlan:
    focus: str
    tasks: List[TaskPlan]
    resources: List[ResourcePlan]


@dataclass(frozen=True)
class ProjectPlan:
    name: str
    description: str
    start_week: int
    end_week: int
    status: str = "planned"
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None


@dataclass(frozen=True)
class CertificationPlan:
    name: str
    provider: str
    due_week: int
    status: str = "planned"
    completion_week: Optional[int] = None
    credential_url: Optional[str] = None
    progress: float = 0.0


@dataclass(frozen=True)
class MetricPlan:
    metric_type: str
    value: float
    unit: str
    week_number: int


@dataclass(frozen=True)
class ApplicationPlan:
    company: str
    role: str
    status: str = "draft"
    week_number: Optional[int] = None
    source: Optional[str] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class PhasePlan:
    name: str
    description: str
    weeks: List[WeekPlan]
    projects: List[ProjectPlan] = field(default_factory=list)
    certifications: List[CertificationPlan] = field(default_factory=list)
    metrics: List[MetricPlan] = field(default_factory=list)


def _week_start_date(week_number: int, *, day_offset: int = 0) -> date:
    if week_number < 1:
        raise ValueError(f"Week numbers must be positive (received {week_number})")
    return START_DATE + timedelta(weeks=week_number - 1, days=day_offset)


def _project_payload(plan: ProjectPlan) -> dict:
    start_date = _week_start_date(plan.start_week)
    due_date = _week_start_date(plan.end_week, day_offset=6)
    return {
        "name": plan.name,
        "description": plan.description,
        "status": plan.status,
        "repo_url": plan.repo_url,
        "demo_url": plan.demo_url,
        "start_date": start_date.isoformat(),
        "due_date": due_date.isoformat(),
    }


def _certification_payload(plan: CertificationPlan) -> dict:
    due_date = _week_start_date(plan.due_week)
    completion_date = (
        _week_start_date(plan.completion_week, day_offset=6)
        if plan.completion_week
        else None
    )
    return {
        "name": plan.name,
        "provider": plan.provider,
        "due_date": due_date.isoformat(),
        "completion_date": completion_date.isoformat() if completion_date else None,
        "status": plan.status,
        "credential_url": plan.credential_url,
        "progress": round(plan.progress, 2),
    }


def _metric_payload(plan: MetricPlan) -> dict:
    recorded_date = _week_start_date(plan.week_number)
    return {
        "metric_type": plan.metric_type,
        "value": plan.value,
        "unit": plan.unit,
        "recorded_date": recorded_date.isoformat(),
    }


def _application_payload(plan: ApplicationPlan) -> dict:
    date_applied = _week_start_date(plan.week_number).isoformat() if plan.week_number else None
    return {
        "company": plan.company,
        "role": plan.role,
        "status": plan.status,
        "source": plan.source,
        "date_applied": date_applied,
        "next_action": plan.next_action,
        "notes": plan.notes,
    }


PHASES: List[PhasePlan] = [
    PhasePlan(
        name="Phase 1 – Hardware Foundations & Modern Embedded C++",
        description=(
            "Calibrate hardware lab, sharpen modern C++ for microcontrollers,"
            " and build disciplined debugging habits. End goal: confidently"
            " shipping bring-up firmware on STM32 and ESP32 targets."
        ),
        weeks=[
            WeekPlan(
                focus="Week 1 – Lab setup, toolchain mastery, baseline measurements",
                tasks=[
                    TaskPlan(
                        title="Provision hardware lab & version-controlled configs",
                        description=(
                            "Assemble STM32 Nucleo, ESP32 DevKit, logic analyzer,"
                            " multimeter. Capture wiring diagrams and udev rules"
                            " in Git-managed lab repo."
                        ),
                        estimated_hours=6.0,
                        ai_prompt=(
                            "Review my lab inventory and suggest safeguards for"
                            " ESD, labeling, and repeatable flashing procedures."
                        ),
                    ),
                    TaskPlan(
                        title="Stand up reproducible build environments",
                        description=(
                            "Install arm-none-eabi toolchain, PlatformIO, Zephyr"
                            " SDK, clang-format hooks. Automate setup via"
                            " devcontainer and shell script."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Inspect my devcontainer.json and post-create commands;"
                            " highlight missing dependencies or caching tricks."
                        ),
                    ),
                    TaskPlan(
                        title="Instrument baseline power & timing measurements",
                        description=(
                            "Bring up reference blink firmware, capture current"
                            " draw vs. supply voltage, and record GPIO toggle"
                            " latency using logic analyzer."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Given oscilloscope captures, estimate ISR jitter and"
                            " recommend probe settings for cleaner edges."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Modern Embedded C++ (Miroslav Vitkovsky)",
                        type="book",
                        notes="Chapters 1-2 for toolchain expectations",
                        url="https://leanpub.com/modern-embedded-cpp",
                    ),
                    ResourcePlan(
                        title="STM32CubeProgrammer & reference manuals",
                        type="docs",
                        notes="RM0433 clock tree review",
                        url="https://www.st.com/en/development-tools/stm32cubeprog.html",
                    ),
                    ResourcePlan(
                        title="PlatformIO advanced debugging webinar",
                        type="video",
                        notes="JTAG workflow refresher",
                        url="https://www.youtube.com/watch?v=rxgWAbh0YXw",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 2 – Modern C++ firmware patterns & memory safety",
                tasks=[
                    TaskPlan(
                        title="Benchmark RAII peripheral wrappers",
                        description=(
                            "Refactor bare-metal drivers to RAII abstractions"
                            " using templates and constexpr config. Compare"
                            " flash/RAM usage to C baseline."
                        ),
                        estimated_hours=6.5,
                        ai_prompt=(
                            "Suggest improvements to my template-based GPIO"
                            " wrapper ensuring zero-cost abstractions."
                        ),
                    ),
                    TaskPlan(
                        title="Static analysis & sanitizers configuration",
                        description=(
                            "Enable clang-tidy, cppcheck, and UBSan/ASan where"
                            " supported via QEMU. Gate CI on static analysis"
                            " profile."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review clang-tidy config for embedded constraints;"
                            " recommend rule adjustments to reduce noise."
                        ),
                    ),
                    TaskPlan(
                        title="Memory layout deep dive",
                        description=(
                            "Analyze linker script, map file, and startup code."
                            " Document boot flow, stack/heap usage, and zero-init"
                            " sections."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Given my linker map, highlight sections to relocate"
                            " to CCM or DTCM for latency gains."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Embedded Artistry linker script guide",
                        type="article",
                        notes="Use for map file annotation",
                        url="https://embeddedartistry.com/blog/2016/10/07/firmware-linker-scripts/",
                    ),
                    ResourcePlan(
                        title="CppCon talk: Zero-cost abstractions on MCUs",
                        type="video",
                        notes="Revisit value semantics patterns",
                        url="https://www.youtube.com/watch?v=_0nIqpSdFBI",
                    ),
                    ResourcePlan(
                        title="QEMU for Cortex-M quickstart",
                        type="docs",
                        notes="Sanitizer instrumentation",
                        url="https://interrupt.memfault.com/blog/qemu-for-cortex-m-development",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 3 – Bare-metal scheduling & CMSIS integration",
                tasks=[
                    TaskPlan(
                        title="Implement cooperative scheduler",
                        description=(
                            "Design tickless cooperative scheduler with event"
                            " queues, priority aging, and unit tests on host."
                        ),
                        estimated_hours=6.0,
                        ai_prompt=(
                            "Analyze scheduler design; suggest guardrails for"
                            " stack overflow detection and trace hooks."
                        ),
                    ),
                    TaskPlan(
                        title="CMSIS HAL deep integration",
                        description=(
                            "Wrap CMSIS drivers with compile-time configs,"
                            " ensuring clock tree abstraction is testable."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review my CMSIS abstraction for test seam quality"
                            " and propose fault-injection hooks."
                        ),
                    ),
                    TaskPlan(
                        title="Latency instrumentation harness",
                        description=(
                            "Add cycle counter-based profiling with ITM/SWO"
                            " output, capturing ISR entry/exit envelopes."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Given SWO trace output, identify bottlenecks and"
                            " suggest buffering strategy."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="ARM CMSIS RTOS v2 design guidelines",
                        type="docs",
                        notes="Scheduler reference",
                        url="https://arm-software.github.io/CMSIS_5/RTOS2/html/index.html",
                    ),
                    ResourcePlan(
                        title="Memfault interrupt latency case study",
                        type="article",
                        notes="Instrumentation patterns",
                        url="https://interrupt.memfault.com/blog/interrupt-latency",
                    ),
                    ResourcePlan(
                        title="Keil ITM/SWO tutorial",
                        type="video",
                        notes="Trace capture setup",
                        url="https://www.youtube.com/watch?v=yJmO7qX0EXM",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 4 – Debugging mastery & fault tolerance",
                tasks=[
                    TaskPlan(
                        title="Advanced debugger scripting",
                        description=(
                            "Craft OpenOCD and pyOCD scripts for automated"
                            " memory dumps, fault log extraction, and SWD"
                            " recovery."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review my OpenOCD TCL scripts and suggest probes"
                            " for hard-fault auto capture."
                        ),
                    ),
                    TaskPlan(
                        title="Hard fault triage playbook",
                        description=(
                            "Implement unified HardFault handler emitting stack"
                            " frames to RTT console and persistent storage."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Given register dump, assist root cause analysis and"
                            " propose guard clauses."
                        ),
                    ),
                    TaskPlan(
                        title="Fault-injection test scenarios",
                        description=(
                            "Simulate brownout, clock failure, and corrupted"
                            " flash to validate recovery pathways."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Design additional fault-injection cases covering"
                            " dual-bank flash swap and watchdog edges."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Definitive Guide to ARM Cortex-M0/M3",
                        type="book",
                        notes="Exception model review",
                        url="https://www.elsevier.com/books/the-definitive-guide-to-arm-cortex-m3-and-cortex-m4-processors/yiu/978-0-12-408082-9",
                    ),
                    ResourcePlan(
                        title="Segger RTT best practices",
                        type="docs",
                        notes="Low-overhead logging",
                        url="https://wiki.segger.com/RTT",
                    ),
                    ResourcePlan(
                        title="Memfault Cortex-M HardFault guide",
                        type="article",
                        notes="HardFault handler template",
                        url="https://interrupt.memfault.com/blog/cortex-m-hardfault-debug",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 5 – Communication stacks & HAL coexistence",
                tasks=[
                    TaskPlan(
                        title="Design SPI/I2C coexistence layer",
                        description=(
                            "Implement arbitration for shared buses with DMA,"
                            " priority inversion safeguards, and unit tests."
                        ),
                        estimated_hours=6.0,
                        ai_prompt=(
                            "Evaluate my bus arbitration design for starvation"
                            " and suggest monitoring hooks."
                        ),
                    ),
                    TaskPlan(
                        title="Protocol analyzers & fixtures",
                        description=(
                            "Capture traces for edge sensors via Saleae and"
                            " decode transactions to confirm timing margins."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Interpret Saleae export; identify anomalies and"
                            " propose firmware timing fixes."
                        ),
                    ),
                    TaskPlan(
                        title="Hardware abstraction validation",
                        description=(
                            "Run hardware-in-loop tests ensuring new bus layer"
                            " survives hot-plug and noise injection."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Design additional HIL scenarios stressing DMA"
                            " concurrency under noise."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="I2C bus specification",
                        type="spec",
                        notes="Check fast-mode plus tables",
                        url="https://www.nxp.com/docs/en/user-guide/UM10204.pdf",
                    ),
                    ResourcePlan(
                        title="Saleae Automation API",
                        type="docs",
                        notes="Script captures",
                        url="https://support.saleae.com/api",
                    ),
                    ResourcePlan(
                        title="ST AN4838 DMA best practices",
                        type="appnote",
                        notes="DMA handshake tuning",
                        url="https://www.st.com/resource/en/application_note/an4838-stm32-dma-controller-stmicroelectronics.pdf",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 6 – Time synchronization & clocking architectures",
                tasks=[
                    TaskPlan(
                        title="Clock tree modeling",
                        description=(
                            "Model PLL configurations, jitter budgets, and"
                            " power implications using Python and STM32CubeMX."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Review PLL sweep script to ensure coverage for"
                            " EMI and sensor interface requirements."
                        ),
                    ),
                    TaskPlan(
                        title="Time synchronization drivers",
                        description=(
                            "Implement PTP/IEEE 1588-lite timestamp capture"
                            " for networked nodes with calibration routine."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Assess timestamping driver; propose compensation"
                            " for oscillator drift vs. reference clock."
                        ),
                    ),
                    TaskPlan(
                        title="Clock fault detection",
                        description=(
                            "Add watchdog for HSE/LSE failure and seamless"
                            " fallback to internal RC with telemetry."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Suggest diagnostic counters to capture clock"
                            " failure frequency and recovery success."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="IEEE 1588 Precision Time Protocol overview",
                        type="article",
                        notes="Timing fundamentals refresher",
                        url="https://www.nist.gov/publications/ieee-1588-precision-time-protocol",
                    ),
                    ResourcePlan(
                        title="STM32 clock configuration guide",
                        type="docs",
                        notes="AN2867 for oscillator design",
                        url="https://www.st.com/resource/en/application_note/cd00221665.pdf",
                    ),
                    ResourcePlan(
                        title="Oscilloscope jitter measurement primer",
                        type="article",
                        notes="Correlate with PLL settings",
                        url="https://www.tek.com/en/blog/what-jitter-and-how-do-i-measure-it",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 7 – Embedded networking fundamentals",
                tasks=[
                    TaskPlan(
                        title="Implement LWIP bare-metal integration",
                        description=(
                            "Port LWIP to STM32 with zero-copy buffers, DMA"
                            " aware memory pools, and unit tests."
                        ),
                        estimated_hours=6.5,
                        ai_prompt=(
                            "Review LWIP port configuration; propose tuning for"
                            " small MTU and TLS overhead."
                        ),
                    ),
                    TaskPlan(
                        title="Network diagnostics toolkit",
                        description=(
                            "Build CLI commands for ping, traceroute, and"
                            " interface stats exposed over UART shell."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Generate test plan validating diagnostics against"
                            " simulated packet loss."
                        ),
                    ),
                    TaskPlan(
                        title="ESP32 Wi-Fi bring-up",
                        description=(
                            "Configure ESP-IDF project with WPA3, OTA update"
                            " hooks, and fallback hotspot provisioning."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Evaluate provisioning UX; suggest secure pairing"
                            " improvements."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="LWIP raw API manual",
                        type="docs",
                        notes="Integrate without RTOS",
                        url="https://www.nongnu.org/lwip/2_1_x/raw_api.html",
                    ),
                    ResourcePlan(
                        title="ESP-IDF security best practices",
                        type="docs",
                        notes="Provisioning patterns",
                        url="https://docs.espressif.com/projects/esp-idf/en/latest/esp32/security/index.html",
                    ),
                    ResourcePlan(
                        title="Embedded networking diagnostics cheatsheet",
                        type="article",
                        notes="CLI command inspiration",
                        url="https://interrupt.memfault.com/blog/embedded-cli",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 8 – Sensor fusion & signal processing foundations",
                tasks=[
                    TaskPlan(
                        title="IMU calibration pipeline",
                        description=(
                            "Implement factory calibration routine capturing"
                            " bias, scale, and temperature coefficients."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Review calibration dataset; suggest statistical"
                            " filters to reject outliers."
                        ),
                    ),
                    TaskPlan(
                        title="Fixed-point DSP primitives",
                        description=(
                            "Port FIR/IIR filters with CMSIS DSP, analyze"
                            " quantization error vs. float baseline."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Given fixed-point coefficients, estimate SNR and"
                            " recommend scaling strategy."
                        ),
                    ),
                    TaskPlan(
                        title="Sensor fusion prototype",
                        description=(
                            "Implement complementary filter on STM32, stream"
                            " quaternion output to desktop visualizer."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Analyze motion capture plots; tune filter gains for"
                            " aggressive motion."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="IMU calibration tutorial (ST)",
                        type="appnote",
                        notes="Extrinsic compensation steps",
                        url="https://www.st.com/resource/en/application_note/dm00083116-stm32f3-gimbal-imu-calibration-stmicroelectronics.pdf",
                    ),
                    ResourcePlan(
                        title="CMSIS DSP library",
                        type="docs",
                        notes="Fixed-point API reference",
                        url="https://arm-software.github.io/CMSIS_5/DSP/html/index.html",
                    ),
                    ResourcePlan(
                        title="PX4 sensor fusion playlist",
                        type="video",
                        notes="Quaternion math refresher",
                        url="https://www.youtube.com/playlist?list=PLybtR63pQR2PzplOQ57Qf8Uai0n1AM5zF",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 9 – Power management & low energy design",
                tasks=[
                    TaskPlan(
                        title="Sleep state orchestration",
                        description=(
                            "Implement STOP/STANDBY transitions, measure wake"
                            " latencies, and document peripheral retention."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review power mode matrix; suggest heuristics for"
                            " predictive sleep scheduling."
                        ),
                    ),
                    TaskPlan(
                        title="Dynamic frequency scaling experiments",
                        description=(
                            "Prototype DFS logic adjusting PLL multipliers"
                            " based on load metrics and deadlines."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Given DFS telemetry, tune policies to avoid missed"
                            " deadlines."
                        ),
                    ),
                    TaskPlan(
                        title="Energy profiling automation",
                        description=(
                            "Set up Joulescope/Otii scripts to batch profile"
                            " firmware revisions and export CSV."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Suggest visualization dashboards for comparing"
                            " energy per task revision."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="STM32 low-power appnote",
                        type="appnote",
                        notes="AN4749 decision tree",
                        url="https://www.st.com/resource/en/application_note/an4749-ultra-low-power-with-stm32l4-series-and-stm32l4-series-mcus-stmicroelectronics.pdf",
                    ),
                    ResourcePlan(
                        title="Otii scripting cookbook",
                        type="docs",
                        notes="Automation tips",
                        url="https://www.qoitech.com/otii-scripting/",
                    ),
                    ResourcePlan(
                        title="Dynamic power management research snapshot",
                        type="paper",
                        notes="Use as inspiration for DFS policies",
                        url="https://dl.acm.org/doi/10.1145/3203221.3203222",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 10 – Bootloaders & secure update foundations",
                tasks=[
                    TaskPlan(
                        title="Blueprint dual-bank bootloader",
                        description=(
                            "Create secure bootloader with image verification,"
                            " rollback protection, and versioned manifests."
                        ),
                        estimated_hours=6.0,
                        ai_prompt=(
                            "Review bootloader state machine; suggest hardening"
                            " around power-loss events."
                        ),
                    ),
                    TaskPlan(
                        title="Cryptographic primitives integration",
                        description=(
                            "Port mbedTLS for ECC signatures, ensure RNG"
                            " entropy sources pass statistical tests."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Audit RNG seeding path; propose health tests per"
                            " NIST guidelines."
                        ),
                    ),
                    TaskPlan(
                        title="FOTA staging pipeline",
                        description=(
                            "Implement host tool for packaging firmware,"
                            " signing, and pushing images to device groups."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Given my staging CLI, suggest CI integration and"
                            " release gating improvements."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="MCUBoot design overview",
                        type="docs",
                        notes="Borrow image manifest ideas",
                        url="https://docs.zephyrproject.org/latest/services/dfu/mcuboot.html",
                    ),
                    ResourcePlan(
                        title="ARM Trusted Firmware-M",
                        type="docs",
                        notes="Secure boot reference",
                        url="https://www.trustedfirmware.org/projects/tf-m/",
                    ),
                    ResourcePlan(
                        title="NIST SP 800-90B",
                        type="spec",
                        notes="Entropy source validation",
                        url="https://csrc.nist.gov/publications/detail/sp/800-90b/final",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 11 – Testing infrastructure & CI enablement",
                tasks=[
                    TaskPlan(
                        title="Host-based simulation harness",
                        description=(
                            "Extend existing simulator with fake drivers,"
                            " golden sensor traces, and property-based tests."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Review property-based test strategy; suggest"
                            " invariants capturing sensor drift."
                        ),
                    ),
                    TaskPlan(
                        title="Hardware test farm automation",
                        description=(
                            "Provision Raspberry Pi runners controlling boards"
                            " via USB, power relays, and measurement gear."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Suggest reliability safeguards for remote flashing"
                            " and automated recovery."
                        ),
                    ),
                    TaskPlan(
                        title="CI dashboards & traces",
                        description=(
                            "Publish build, test, and energy metrics to Grafana"
                            " with historical comparison."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review Grafana queries; propose SLO-style alerts"
                            " for regressions."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Renode & Robot Framework guide",
                        type="article",
                        notes="Simulation inspiration",
                        url="https://interrupt.memfault.com/blog/renode-for-testing",
                    ),
                    ResourcePlan(
                        title="GitHub Actions self-hosted runners",
                        type="docs",
                        notes="Pi farm management",
                        url="https://docs.github.com/actions/hosting-your-own-runners/managing-self-hosted-runners",
                    ),
                    ResourcePlan(
                        title="Grafana streaming metrics tutorial",
                        type="video",
                        notes="Dashboards refresher",
                        url="https://grafana.com/go/learn/grafana-fundamentals/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 12 – Safety basics & design for reliability",
                tasks=[
                    TaskPlan(
                        title="Failure Mode and Effects Analysis (FMEA)",
                        description=(
                            "Conduct FMEA on core subsystems, log mitigations"
                            " and residual risk in safety register."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review FMEA worksheet; challenge risk priority"
                            " numbers and coverage."
                        ),
                    ),
                    TaskPlan(
                        title="Watchdog strategy consolidation",
                        description=(
                            "Integrate multi-stage watchdogs (windowed +"
                            " software) with service diagnostics."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Suggest metrics exposing watchdog near-expiry"
                            " events and false positives."
                        ),
                    ),
                    TaskPlan(
                        title="Brownout & EMI resilience",
                        description=(
                            "Design brownout detection, logging, and recovery"
                            " tests with EMI injection bench."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Given oscilloscope captures, identify EMI coupling"
                            " paths and shielding strategies."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="ISO 26262 overview",
                        type="course",
                        notes="Safety vocabulary",
                        url="https://www.youtube.com/watch?v=pemLkAMPx7Q",
                    ),
                    ResourcePlan(
                        title="NXP watchdog design guide",
                        type="appnote",
                        notes="Best practices",
                        url="https://www.nxp.com/docs/en/application-note/AN4619.pdf",
                    ),
                    ResourcePlan(
                        title="EMC troubleshooting handbook",
                        type="book",
                        notes="Chapters on shielding",
                        url="https://www.sae.org/publications/books/content/r-146/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 13 – Phase consolidation & portfolio artifact",
                tasks=[
                    TaskPlan(
                        title="Refactor showcase firmware",
                        description=(
                            "Clean architecture of phase project, add"
                            " documentation, diagrams, and CI badges."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review README and architecture diagrams; suggest"
                            " clarity improvements for recruiters."
                        ),
                    ),
                    TaskPlan(
                        title="Case study write-up",
                        description=(
                            "Draft blog or whitepaper summarizing lessons,"
                            " architecture decisions, and quantified metrics"
                            " collected during instrumentation efforts."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Edit my case-study outline for narrative arc and"
                            " quantifiable outcomes."
                        ),
                    ),
                    TaskPlan(
                        title="Phase retrospective & backlog grooming",
                        description=(
                            "Hold retro, capture metrics, adjust backlog"
                            " priorities for next phase."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Analyze retro notes; produce action items and"
                            " guardrails for Phase 2."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Technical writing checklist",
                        type="article",
                        notes="Narrative polish",
                        url="https://jacobian.org/2013/feb/28/writing-technical-documentation/",
                    ),
                    ResourcePlan(
                        title="Notion project retrospective template",
                        type="template",
                        notes="Frame retro meeting",
                        url="https://www.notion.so/templates/project-retrospective",
                    ),
                    ResourcePlan(
                        title="Obsidian publishing guide",
                        type="docs",
                        notes="Share notes publicly",
                        url="https://help.obsidian.md/Publishing",
                    ),
                ],
            ),
        ],
        projects=[
            ProjectPlan(
                name="LabOps Automation Suite",
                description=(
                    "GitOps-managed lab setup for the MSI B850M + Ryzen 7"
                    " 7700 rig, covering BIOS profiles, dual-boot imaging,"
                    " CUDA/RTX enablement, and repeatable VS Code"
                    " devcontainer provisioning."
                ),
                start_week=1,
                end_week=4,
                status="in_progress",
                repo_url="https://github.com/khashyap0803/embedded-labops",
            ),
            ProjectPlan(
                name="Deterministic Timing Harness",
                description=(
                    "Cycle-accurate STM32/ESP32 harness that records power,"
                    " jitter, and ISR latency via Saleae + AMD PMU traces;"
                    " feeds Grafana dashboards for regression tracking."
                ),
                start_week=2,
                end_week=6,
                status="in_progress",
                repo_url="https://github.com/khashyap0803/deterministic-harness",
            ),
            ProjectPlan(
                name="Debug Resilience Playbook",
                description=(
                    "OpenOCD/pyOCD automation scripts plus Notion SOPs for"
                    " fault triage, covering brownouts, flash corruption,"
                    " and SWD recovery on the lab boards."
                ),
                start_week=4,
                end_week=8,
                status="planned",
                repo_url="https://github.com/khashyap0803/debug-playbook",
            ),
            ProjectPlan(
                name="Multi-sensor Baseline Kit",
                description=(
                    "Bring-up of IMU/pressure/temp stack on STM32 + ESP32"
                    " with shared SPI/I2C arbitration, automated tests, and"
                    " Grafana-exported energy metrics."
                ),
                start_week=7,
                end_week=13,
                status="planned",
                repo_url="https://github.com/khashyap0803/sensor-baseline",
            ),
        ],
        certifications=[
            CertificationPlan(
                name="ST MCU Developer – Level 1",
                provider="STMicroelectronics Academy",
                due_week=11,
                status="in_progress",
                progress=0.35,
            ),
        ],
        metrics=[
            MetricPlan(
                metric_type="phase1_hours_logged",
                value=78.0,
                unit="hours",
                week_number=4,
            ),
            MetricPlan(
                metric_type="lab_automation_pass_rate",
                value=0.92,
                unit="ratio",
                week_number=13,
            ),
        ],
    ),
    PhasePlan(
        name="Phase 2 – Real-Time Systems & Connected Firmware",
        description=(
            "Deepen RTOS mastery, design resilient connectivity stacks, and"
            " harden security for fleet-ready firmware. Culminates in a"
            " production-quality Zephyr/FreeRTOS application spanning CAN,"
            " Ethernet, BLE, and secure provisioning."
        ),
        weeks=[
            WeekPlan(
                focus="Week 14 – Zephyr RTOS architecture & board bring-up",
                tasks=[
                    TaskPlan(
                        title="Custom Zephyr board definition",
                        description=(
                            "Author Devicetree overlays, Kconfig fragments,"
                            " and pin-control for bespoke STM32 board."
                        ),
                        estimated_hours=6.0,
                        ai_prompt=(
                            "Inspect my Zephyr board port; identify missing"
                            " regulators, sensors, or power domains."
                        ),
                    ),
                    TaskPlan(
                        title="Kernel services tour",
                        description=(
                            "Prototype threads, ISRs, workqueues, fibers,"
                            " and MEMS pipelines with tracing hooks."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Suggest instrumentation to visualize context"
                            " switches and ISR latency in Zephyr Trace."
                        ),
                    ),
                    TaskPlan(
                        title="West build automation",
                        description=(
                            "Script multi-target builds, unit tests, and"
                            " packaging via west and CMake presets."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Optimize my west manifest for dependency reuse"
                            " across targets."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Zephyr Devicetree primer",
                        type="docs",
                        notes="Overlay syntax refresher",
                        url="https://docs.zephyrproject.org/latest/build/dts/index.html",
                    ),
                    ResourcePlan(
                        title="Zephyr tracing & logging guide",
                        type="docs",
                        notes="Enable system view",
                        url="https://docs.zephyrproject.org/latest/services/tracing/index.html",
                    ),
                    ResourcePlan(
                        title="Memfault Zephyr bring-up checklist",
                        type="article",
                        notes="Double-check porting steps",
                        url="https://interrupt.memfault.com/blog/zephyr-porting",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 15 – Deterministic scheduling & time partitioning",
                tasks=[
                    TaskPlan(
                        title="Latency budgeting & rate-monotonic analysis",
                        description=(
                            "Compute task deadlines, CPU utilization, and"
                            " blocking time using RMA spreadsheets."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review my RMA model; warn about overload and"
                            " priority inversion risks."
                        ),
                    ),
                    TaskPlan(
                        title="Time-triggered executor",
                        description=(
                            "Implement static schedule table with slack-stealing"
                            " fallback for best-effort tasks."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Assess executor design; propose monitoring for"
                            " missed frames."
                        ),
                    ),
                    TaskPlan(
                        title="Tracing & visualization",
                        description=(
                            "Capture Segger SystemView timeline, annotate"
                            " context switches, and publish analysis."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Interpret SystemView export; highlight anomalies"
                            " and improvements."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Liu & Layland RMA paper",
                        type="paper",
                        notes="Theory refresher",
                        url="https://people.cs.pitt.edu/~melhem/courses/2740/liu-layland.pdf",
                    ),
                    ResourcePlan(
                        title="SystemView tutorials",
                        type="video",
                        notes="Visualization walkthrough",
                        url="https://www.youtube.com/watch?v=uH9K6gZHRk0",
                    ),
                    ResourcePlan(
                        title="Zephyr scheduling internals",
                        type="docs",
                        notes="Scheduler deep dive",
                        url="https://docs.zephyrproject.org/latest/kernel/services/scheduling/index.html",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 16 – High-performance drivers & DMA pipelines",
                tasks=[
                    TaskPlan(
                        title="Chained DMA transfers",
                        description=(
                            "Implement cyclic DMA for ADC and audio data with"
                            " double-buffered synchronization."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Review DMA configuration; recommend alignment"
                            " constraints for cache coherence."
                        ),
                    ),
                    TaskPlan(
                        title="Zero-copy sensor framework",
                        description=(
                            "Design producer-consumer queues for high-rate"
                            " sensor fusion with backpressure."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Assess queue API; propose bounded latency"
                            " guarantees."
                        ),
                    ),
                    TaskPlan(
                        title="Driver fatigue tests",
                        description=(
                            "Run soak tests via pytest-benchmark capturing"
                            " throughput, drops, and CPU usage."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Given benchmark CSV, identify regressions and"
                            " suggest tuning knobs."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="ST AN4031 DMA cookbook",
                        type="appnote",
                        notes="Linked list strategies",
                        url="https://www.st.com/resource/en/application_note/an4031.pdf",
                    ),
                    ResourcePlan(
                        title="Zephyr sensor subsystem",
                        type="docs",
                        notes="Driver patterns",
                        url="https://docs.zephyrproject.org/latest/reference/peripherals/sensor.html",
                    ),
                    ResourcePlan(
                        title="pytest-benchmark documentation",
                        type="docs",
                        notes="Profiling helpers",
                        url="https://pytest-benchmark.readthedocs.io/en/latest/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 17 – CAN/CAN-FD & automotive-grade networking",
                tasks=[
                    TaskPlan(
                        title="CAN stack integration",
                        description=(
                            "Implement CAN-FD driver with ISO-TP, UDS"
                            " diagnostics, and acceptance filters."
                        ),
                        estimated_hours=6.0,
                        ai_prompt=(
                            "Evaluate CAN filter strategy; suggest DBC tuning"
                            " for critical frames."
                        ),
                    ),
                    TaskPlan(
                        title="Network load simulation",
                        description=(
                            "Use CANoe or cantools to simulate bus loads,"
                            " error frames, and measure latency budgets."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Interpret bus load metrics; propose fail-safe"
                            " behaviors on error passive."
                        ),
                    ),
                    TaskPlan(
                        title="Diagnostics tooling",
                        description=(
                            "Build PC-side CLI to flash ECUs via UDS, capture"
                            " DTCs, and log sessions."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Suggest ergonomics improvements to UDS CLI and"
                            " error handling."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Vector CANoe essentials",
                        type="course",
                        notes="Simulation techniques",
                        url="https://elearning.vector.com/mod/page/view.php?id=1734",
                    ),
                    ResourcePlan(
                        title="Vector CAN FD knowledge base",
                        type="article",
                        notes="Protocol nuances",
                        url="https://www.vector.com/int/en/know-how/technical-articles/can-fd/",
                    ),
                    ResourcePlan(
                        title="cantools usage guide",
                        type="docs",
                        notes="Automate DBC parsing",
                        url="https://cantools.readthedocs.io/en/latest/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 18 – Industrial Ethernet & TSN exploration",
                tasks=[
                    TaskPlan(
                        title="Profinet/TSN reconnaissance",
                        description=(
                            "Prototype TSN schedule using Zephyr Qav/Qbv"
                            " features for deterministic Ethernet."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Review TSN gate schedule; highlight conflicts"
                            " with CAN deadlines."
                        ),
                    ),
                    TaskPlan(
                        title="Edge switch configuration lab",
                        description=(
                            "Configure managed switch QoS, VLANs, and PTP"
                            " boundary clock roles."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Given switch config, suggest monitoring for drift"
                            " and congestion."
                        ),
                    ),
                    TaskPlan(
                        title="Network compliance tests",
                        description=(
                            "Run Wireshark dissectors, packet capture scripts,"
                            " and conformance checks."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Interpret Wireshark traces; identify jitter"
                            " sources and countermeasures."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Time-Sensitive Networking tutorial",
                        type="article",
                        notes="Primer on IEEE 802.1 Qbv/Qci",
                        url="https://www.ni.com/en-us/innovations/white-papers/16/introduction-to-time-sensitive-networking--tsn-.html",
                    ),
                    ResourcePlan(
                        title="Zephyr TSN samples",
                        type="docs",
                        notes="Example configs",
                        url="https://docs.zephyrproject.org/latest/samples/net/tsn/README.html",
                    ),
                    ResourcePlan(
                        title="Wireshark TSN dissector",
                        type="docs",
                        notes="Capture analysis",
                        url="https://wiki.wireshark.org/Time-Sensitive_Networking",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 19 – Bluetooth Low Energy & provisioning UX",
                tasks=[
                    TaskPlan(
                        title="BLE stack deep dive",
                        description=(
                            "Implement Zephyr Bluetooth host with secure"
                            " connections, GATT services, and DFU."
                        ),
                        estimated_hours=6.0,
                        ai_prompt=(
                            "Review GATT layout; propose characteristics for"
                            " diagnostics and OTA."
                        ),
                    ),
                    TaskPlan(
                        title="Provisioning companion app",
                        description=(
                            "Build Flutter or React Native app to provision"
                            " Wi-Fi credentials via BLE."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Critique onboarding UX; suggest accessibility"
                            " improvements."
                        ),
                    ),
                    TaskPlan(
                        title="RF characterization",
                        description=(
                            "Measure BLE RSSI vs. distance, interference,"
                            " and antenna orientation."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Interpret RF sweep data; recommend antenna"
                            " placement tweaks."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Bluetooth Core Specification summary",
                        type="spec",
                        notes="Security sections",
                        url="https://www.bluetooth.com/specifications/specs/",
                    ),
                    ResourcePlan(
                        title="Nordic DevAcademy BLE course",
                        type="course",
                        notes="Procedural refresher",
                        url="https://academy.nordicsemi.com/",
                    ),
                    ResourcePlan(
                        title="Flutter BLE best practices",
                        type="article",
                        notes="App scaffolding",
                        url="https://medium.com/flutter-community/ble-in-flutter-8769f55c1af9",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 20 – Secure communications & provisioning hardening",
                tasks=[
                    TaskPlan(
                        title="TLS stack integration",
                        description=(
                            "Enable mbedTLS with session caching, hardware"
                            " acceleration, and certificate rotation."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Review TLS configuration; suggest cipher suite"
                            " adjustments for resource limits."
                        ),
                    ),
                    TaskPlan(
                        title="Secure credential provisioning",
                        description=(
                            "Implement Just-In-Time provisioning with TPM/ATECC"
                            " secure elements and attestation."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Assess attestation flow; propose anti-cloning"
                            " safeguards."
                        ),
                    ),
                    TaskPlan(
                        title="Pen test & threat modeling",
                        description=(
                            "Conduct STRIDE threat model, run fuzzers on protocol"
                            " handlers, and document mitigations."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review threat model; highlight missing abuse"
                            " cases."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="mbedTLS configuration manual",
                        type="docs",
                        notes="Memory footprint tuning",
                        url="https://tls.mbed.org/kb/how-to/configure-mbedtls",
                    ),
                    ResourcePlan(
                        title="Microchip ATECC608A design guide",
                        type="appnote",
                        notes="Secure element patterns",
                        url="https://ww1.microchip.com/downloads/en/Appnotes/Atmel-8987-CryptoAuth-ATECC608A-DesignConsiderations-ApplicationNote.pdf",
                    ),
                    ResourcePlan(
                        title="OWASP firmware security testing",
                        type="guide",
                        notes="Threat modeling prompts",
                        url="https://owasp.org/www-project-internet-of-things/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 21 – Fleet update infrastructure & DevOps",
                tasks=[
                    TaskPlan(
                        title="Update orchestration server",
                        description=(
                            "Deploy cloud service (AWS IoT Jobs/Azure IoT Hub)"
                            " for staged rollouts and phased updates."
                        ),
                        estimated_hours=5.5,
                        ai_prompt=(
                            "Evaluate rollout strategy; propose guarding"
                            " against network partitions."
                        ),
                    ),
                    TaskPlan(
                        title="Progressive rollout automation",
                        description=(
                            "Script blue/green, canary, and cohort-based update"
                            " policies driven by metrics."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review canary pipeline; suggest success metrics"
                            " and abort triggers."
                        ),
                    ),
                    TaskPlan(
                        title="Device health telemetry",
                        description=(
                            "Publish heartbeat, error counters, and version"
                            " info to observability stack."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Recommend telemetry compacting strategies for"
                            " constrained links."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="AWS IoT Jobs workshop",
                        type="hands-on",
                        notes="Rollout automation",
                        url="https://catalog.workshops.aws/iot-jobs/en-US",
                    ),
                    ResourcePlan(
                        title="Azure Device Update patterns",
                        type="docs",
                        notes="Cohort design",
                        url="https://learn.microsoft.com/azure/iot-hub-device-update/",
                    ),
                    ResourcePlan(
                        title="Grafana Loki logs for IoT",
                        type="article",
                        notes="Centralized telemetry",
                        url="https://grafana.com/blog/2022/10/18/collecting-logs-from-iot-devices/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 22 – Data pipelines & storage durability",
                tasks=[
                    TaskPlan(
                        title="Filesystem resilience",
                        description=(
                            "Evaluate LittleFS vs. FAT, simulate power-loss,"
                            " and profile wear-leveling."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Interpret filesystem stress logs; propose flush"
                            " strategies."
                        ),
                    ),
                    TaskPlan(
                        title="Structured telemetry encoding",
                        description=(
                            "Adopt CBOR/Protobuf with versioning, delta"
                            " compression, and test vectors."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review schema evolution plan; suggest backward"
                            " compatibility tests."
                        ),
                    ),
                    TaskPlan(
                        title="Edge analytics groundwork",
                        description=(
                            "Implement sliding-window analytics on-device"
                            " for anomaly detection cues."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Evaluate anomaly detectors; recommend thresholds"
                            " and false-positive tactics."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="LittleFS design paper",
                        type="whitepaper",
                        notes="Crash-consistency fundamentals",
                        url="https://github.com/littlefs-project/littlefs/blob/master/DESIGN.md",
                    ),
                    ResourcePlan(
                        title="CBOR RFC 7049",
                        type="spec",
                        notes="Encoding reference",
                        url="https://www.rfc-editor.org/rfc/rfc7049",
                    ),
                    ResourcePlan(
                        title="TinyML anomaly detection sample",
                        type="repo",
                        notes="Accelerate edge analytics",
                        url="https://github.com/tinyMLx/courseware",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 23 – Observability, logging, and remote diagnostics",
                tasks=[
                    TaskPlan(
                        title="Unified logging schema",
                        description=(
                            "Design structured logging macros with severity,"
                            " module tags, and log streaming over RTT/MQTT."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review logging schema; suggest sampling and"
                            " suppression tactics."
                        ),
                    ),
                    TaskPlan(
                        title="Crash dump & corefile export",
                        description=(
                            "Automate coredump capture, symbol resolution,"
                            " and upload to cloud bucket."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Critique dump pipeline; recommend data retention"
                            " policies."
                        ),
                    ),
                    TaskPlan(
                        title="Remote debug toolkit",
                        description=(
                            "Implement remote shell, feature flags, and trace"
                            " controls gated by RBAC."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Evaluate remote shell security; suggest auditing"
                            " hooks."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Memfault diagnostic stack guides",
                        type="docs",
                        notes="Crash dump export reference",
                        url="https://docs.memfault.com/docs/introduction/introduction",
                    ),
                    ResourcePlan(
                        title="Google Cloud logging structured fields",
                        type="docs",
                        notes="Schema inspiration",
                        url="https://cloud.google.com/logging/docs/structured-logging",
                    ),
                    ResourcePlan(
                        title="OWASP access control cheat sheet",
                        type="article",
                        notes="Secure remote tooling",
                        url="https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 24 – Gateway integration & heterogeneous compute",
                tasks=[
                    TaskPlan(
                        title="Linux gateway handshake",
                        description=(
                            "Implement MQTT or gRPC bridge to Jetson/RPi edge"
                            " gateway with secure tunneling."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review bridge protocol; propose retries and"
                            " offline caching strategies."
                        ),
                    ),
                    TaskPlan(
                        title="Edge containerization",
                        description=(
                            "Package gateway services via Docker/Podman,"
                            " configure systemd supervision."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Optimize container footprint; suggest multi-arch"
                            " build pipelines."
                        ),
                    ),
                    TaskPlan(
                        title="Secure gateway firmware channel",
                        description=(
                            "Implement mutual auth between MCU and gateway"
                            " with cert pinning and rate limits."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review handshake logs; propose intrusion"
                            " detection telemetry."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="NVIDIA Jetson security best practices",
                        type="docs",
                        notes="Gateway hardening",
                        url="https://docs.nvidia.com/jetson/archives/r34.1/DeveloperGuide/",
                    ),
                    ResourcePlan(
                        title="MQTT essentials whitepaper",
                        type="whitepaper",
                        notes="Messaging semantics",
                        url="https://mqtt.org/documentation",
                    ),
                    ResourcePlan(
                        title="Podman on edge devices",
                        type="article",
                        notes="Containerization tips",
                        url="https://www.redhat.com/en/blog/running-containers-resource-constrained-environments",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 25 – Mixed-criticality & virtualization",
                tasks=[
                    TaskPlan(
                        title="Static partitioning prototype",
                        description=(
                            "Experiment with ARM TrustZone or MPU regions to"
                            " isolate safety-critical tasks."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review partition map; highlight potential"
                            " privilege escalation paths."
                        ),
                    ),
                    TaskPlan(
                        title="Hypervisor evaluation",
                        description=(
                            "Assess ACRN/Jailhouse or SafeRTOS partitioning"
                            " for multi-tenant workloads."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Compare hypervisor candidates; recommend selection"
                            " criteria based on workload."
                        ),
                    ),
                    TaskPlan(
                        title="Safety case scaffolding",
                        description=(
                            "Draft safety case argumentation linking hazards,"
                            " mitigations, and evidence artifacts."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Critique safety case draft; suggest evidence gaps"
                            " to close."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="ARM TrustZone for Cortex-M guide",
                        type="docs",
                        notes="Partitioning basics",
                        url="https://developer.arm.com/documentation/101369/latest/",
                    ),
                    ResourcePlan(
                        title="Jailhouse hypervisor overview",
                        type="docs",
                        notes="Mixed-criticality case studies",
                        url="https://github.com/siemens/jailhouse",
                    ),
                    ResourcePlan(
                        title="Safety case patterns (SINTEF)",
                        type="paper",
                        notes="Argument structure",
                        url="https://www.sintef.no/globalassets/project/safecap/safety-case-patterns.pdf",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 26 – Phase consolidation, demos, and midterm review",
                tasks=[
                    TaskPlan(
                        title="End-to-end integration demo",
                        description=(
                            "Record video demo of MCU ↔ gateway ↔ cloud"
                            " workflow with monitoring dashboards."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review demo script; suggest narrative emphasis"
                            " for hiring managers."
                        ),
                    ),
                    TaskPlan(
                        title="Documentation sprint",
                        description=(
                            "Polish ADRs, interfaces, and playbooks; ensure"
                            " onboarding readiness."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Proofread docs; recommend diagrams to add."
                        ),
                    ),
                    TaskPlan(
                        title="Midterm skills assessment",
                        description=(
                            "Run skills gap analysis, benchmark vs. original"
                            " objectives, and adjust roadmap."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Evaluate assessment results; prioritize focus"
                            " areas for Phase 3."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Pitching engineering work",
                        type="video",
                        notes="Demo storytelling",
                        url="https://www.youtube.com/watch?v=k8X8tH6vOA0",
                    ),
                    ResourcePlan(
                        title="Architecture Decision Record template",
                        type="template",
                        notes="Ensure consistency",
                        url="https://adr.github.io/madr/",
                    ),
                    ResourcePlan(
                        title="Roadmap retrospective worksheet",
                        type="worksheet",
                        notes="Guide review meeting",
                        url="https://miro.com/miroverse/product-roadmap-retrospective/",
                    ),
                ],
            ),
        ],
    ),
    PhasePlan(
        name="Phase 3 – Edge Intelligence, Safety & Manufacturing Readiness",
        description=(
            "Blend TinyML with safety-critical practices, harden products for"
            " compliance, and build manufacturing-grade test infrastructure."
            " End state: intelligent, secure firmware paired with production"
            " test rigs and certification artefacts."
        ),
        weeks=[
            WeekPlan(
                focus="Week 27 – TinyML foundations on Cortex-M",
                tasks=[
                    TaskPlan(
                        title="Dataset curation & labeling",
                        description=(
                            "Collect sensor datasets (IMU, audio), perform"
                            " labeling in Edge Impulse, and version datasets."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review dataset stats; recommend augmentation"
                            " strategies and balancing."
                        ),
                    ),
                    TaskPlan(
                        title="Model prototyping",
                        description=(
                            "Train baseline models using TensorFlow/Keras,"
                            " evaluate accuracy/F1, document pipeline."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Analyze training logs; propose architecture"
                            " tweaks for latency constraints."
                        ),
                    ),
                    TaskPlan(
                        title="TFLite Micro deployment",
                        description=(
                            "Integrate TFLM interpreter on STM32, measure"
                            " inference latency and memory footprint."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review TFLM arena configuration; suggest memory"
                            " savings without accuracy loss."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Edge Impulse data operations",
                        type="docs",
                        notes="Dataset versioning",
                        url="https://docs.edgeimpulse.com/docs",
                    ),
                    ResourcePlan(
                        title="TinyML Cookbook",
                        type="book",
                        notes="Chapters on MCU deployment",
                        url="https://www.oreilly.com/library/view/tinyml-cookbook/9781098100824/",
                    ),
                    ResourcePlan(
                        title="TensorFlow Lite Micro examples",
                        type="repo",
                        notes="Reference code",
                        url="https://github.com/tensorflow/tflite-micro",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 28 – Optimization, quantization, and benchmarks",
                tasks=[
                    TaskPlan(
                        title="Quantization-aware training",
                        description=(
                            "Apply QAT and post-training quantization, compare"
                            " int8 vs. float models across metrics."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Inspect calibration pipeline; suggest histogram"
                            " bins and representative datasets."
                        ),
                    ),
                    TaskPlan(
                        title="Operator fusion & optimization",
                        description=(
                            "Implement CMSIS-NN kernels, evaluate speedups,"
                            " and profile with mcycle counters."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review profiling output; recommend kernel fusion"
                            " or tiling strategies."
                        ),
                    ),
                    TaskPlan(
                        title="Benchmark harness",
                        description=(
                            "Build automated benchmarking to compare models"
                            " vs. latency, energy, and accuracy budgets."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Suggest visualizations and statistical tests for"
                            " benchmark results."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="CMSIS-NN optimization guide",
                        type="docs",
                        notes="Kernel tuning",
                        url="https://arm-software.github.io/CMSIS_5/NN/html/index.html",
                    ),
                    ResourcePlan(
                        title="TensorFlow Model Optimization Toolkit",
                        type="docs",
                        notes="Quantization recipes",
                        url="https://www.tensorflow.org/model_optimization",
                    ),
                    ResourcePlan(
                        title="MLPerf Tiny benchmark",
                        type="benchmark",
                        notes="Compare targets",
                        url="https://mlcommons.org/en/inference-tiny/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 29 – Sensor fusion with ML & adaptive algorithms",
                tasks=[
                    TaskPlan(
                        title="Feature engineering",
                        description=(
                            "Design domain-specific features, run SHAP/LIME"
                            " explainability to justify selections."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review feature importance; recommend pruning"
                            " while retaining accuracy."
                        ),
                    ),
                    TaskPlan(
                        title="Adaptive filtering",
                        description=(
                            "Blend Kalman filter with ML classifier outputs"
                            " for robust predictions under noise."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Evaluate fusion pipeline; suggest tuning for"
                            " dynamic motion."
                        ),
                    ),
                    TaskPlan(
                        title="On-device learning experiments",
                        description=(
                            "Prototype incremental learning or personalization"
                            " with cautious memory usage."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Assess personalization strategy; warn about"
                            " catastrophic forgetting."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Sensor fusion architectures",
                        type="paper",
                        notes="Combine model & Bayesian filters",
                        url="https://arxiv.org/abs/2009.08264",
                    ),
                    ResourcePlan(
                        title="SHAP explainability docs",
                        type="docs",
                        notes="Interpretation tools",
                        url="https://shap.readthedocs.io/en/latest/",
                    ),
                    ResourcePlan(
                        title="Edge personalization case studies",
                        type="article",
                        notes="Ideas for on-device learning",
                        url="https://www.edge-ai-vision.com/2021/04/on-device-learning/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 30 – Embedded computer vision & perception",
                tasks=[
                    TaskPlan(
                        title="Camera interface bring-up",
                        description=(
                            "Configure DCMI/CSI interface, tune exposure,"
                            " and verify frame capture to RAM."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review camera timing; suggest buffer strategy"
                            " for low-latency inferencing."
                        ),
                    ),
                    TaskPlan(
                        title="Model selection",
                        description=(
                            "Port efficient CNN (MobileNetV3, Tiny-YOLO) using"
                            " TVM or TFLM, profile FPS and memory."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Compare candidate models; recommend pruning or"
                            " distillation tactics."
                        ),
                    ),
                    TaskPlan(
                        title="Pipeline optimization",
                        description=(
                            "Use DMA2D, pixel format converters, and hardware"
                            " accelerators to minimize CPU stalls."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Inspect pipeline; suggest double-buffering or"
                            " hardware acceleration improvements."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="OpenMV & STM32 camera app notes",
                        type="appnote",
                        notes="Camera bring-up tips",
                        url="https://www.openmv.io/pages/download",
                    ),
                    ResourcePlan(
                        title="TVM microTVM tutorial",
                        type="docs",
                        notes="Deploy optimized models",
                        url="https://tvm.apache.org/docs/tutorial/micro/micro_tflite.html",
                    ),
                    ResourcePlan(
                        title="MobileNetV3 paper",
                        type="paper",
                        notes="Model characteristics",
                        url="https://arxiv.org/abs/1905.02244",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 31 – Functional safety standards deep dive",
                tasks=[
                    TaskPlan(
                        title="Safety plan creation",
                        description=(
                            "Draft ISO 26262/IEC 61508 aligned safety plan,"
                            " define ASIL targets and work products."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review safety plan; identify missing stakeholder"
                            " roles or deliverables."
                        ),
                    ),
                    TaskPlan(
                        title="Software safety requirements",
                        description=(
                            "Refine requirements with traceability to hazards"
                            " and verification methods."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Critique requirement wording; ensure testable and"
                            " unambiguous phrasing."
                        ),
                    ),
                    TaskPlan(
                        title="Verification planning",
                        description=(
                            "Map verification techniques (MC/DC, fault"
                            " injection) to requirements with tooling plan."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Evaluate verification matrix; suggest evidence"
                            " gathering strategies."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="ISO 26262 part summaries",
                        type="guide",
                        notes="High-level orientation",
                        url="https://www.iso.org/standard/43464.html",
                    ),
                    ResourcePlan(
                        title="Functional safety pocket guide",
                        type="article",
                        notes="Terminology refresher",
                        url="https://resources.sei.cmu.edu/library/asset-view.cfm?assetid=628425",
                    ),
                    ResourcePlan(
                        title="AbsInt MC/DC tooling overview",
                        type="docs",
                        notes="Verification tooling",
                        url="https://www.absint.com/do178c/coverage.html",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 32 – Diagnostic coverage & redundancy",
                tasks=[
                    TaskPlan(
                        title="Diagnostic coverage calculations",
                        description=(
                            "Quantify single-point fault metrics (SPFM) and"
                            " latent fault metrics (LFM)."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review coverage spreadsheet; flag unrealistic"
                            " assumptions."
                        ),
                    ),
                    TaskPlan(
                        title="Redundant monitoring",
                        description=(
                            "Implement dual-channel sensing with cross checks"
                            " and degrade modes."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Assess redundancy design; propose diagnostic"
                            " hooks."
                        ),
                    ),
                    TaskPlan(
                        title="Fault injection campaign",
                        description=(
                            "Automate bit flips, stuck-at faults, sensor"
                            " freezes, and measure detection latency."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review campaign results; identify blind spots"
                            " needing mitigation."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Diagnostic coverage explained",
                        type="article",
                        notes="Metrics refresher",
                        url="https://www.embedded.com/functional-safety-diagnostic-coverage-explained/",
                    ),
                    ResourcePlan(
                        title="ASIL decomposition reference",
                        type="docs",
                        notes="Redundancy design",
                        url="https://www.mathworks.com/help/slcheck/ug/asil-decomposition.html",
                    ),
                    ResourcePlan(
                        title="Firmware fault injection patterns",
                        type="article",
                        notes="Testing inspiration",
                        url="https://interrupt.memfault.com/blog/fault-injection",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 33 – Cybersecurity operations & SBOM management",
                tasks=[
                    TaskPlan(
                        title="SBOM generation & automation",
                        description=(
                            "Produce SPDX/CycloneDX SBOMs via build tooling"
                            " and integrate into CI."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review SBOM content; ensure license and patch"
                            " metadata completeness."
                        ),
                    ),
                    TaskPlan(
                        title="Vulnerability triage playbook",
                        description=(
                            "Set up dependency scanning, CVE feeds, and"
                            " response processes."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Assess triage workflow; suggest automation for"
                            " notification and patch validation."
                        ),
                    ),
                    TaskPlan(
                        title="Secure boot attestation audits",
                        description=(
                            "Verify secure boot logs, certificate rotation,"
                            " and tamper detection instrumentation."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Inspect attestation reports; recommend additional"
                            " integrity checks."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="CycloneDX CLI",
                        type="docs",
                        notes="Automate SBOMs",
                        url="https://cyclonedx.org/tool-center/",
                    ),
                    ResourcePlan(
                        title="OWASP IoT security verification standard",
                        type="standard",
                        notes="Checklist for security ops",
                        url="https://owasp.org/www-project-iot-security-verification-standard/",
                    ),
                    ResourcePlan(
                        title="NIST Cybersecurity Framework",
                        type="guide",
                        notes="Align processes",
                        url="https://www.nist.gov/cyberframework",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 34 – Production test fixtures & DFM",
                tasks=[
                    TaskPlan(
                        title="Test fixture design",
                        description=(
                            "Design pogo-pin bed-of-nails fixture with"
                            " automated flashing and boundary scan."
                        ),
                        estimated_hours=5.0,
                        ai_prompt=(
                            "Review fixture CAD/BOM; suggest reliability"
                            " improvements for throughput."
                        ),
                    ),
                    TaskPlan(
                        title="Manufacturing test scripts",
                        description=(
                            "Create automated tests covering electrical,"
                            " functional, and calibration steps."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Assess script coverage; propose metrics for"
                            " yield tracking."
                        ),
                    ),
                    TaskPlan(
                        title="DFM review",
                        description=(
                            "Conduct design-for-manufacture review with CM,"
                            " capture modifications for assembly ease."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review DFM checklist; highlight risk areas for"
                            " assembly variation."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Adafruit manufacturing fixture overview",
                        type="article",
                        notes="Fixture inspiration",
                        url="https://blog.adafruit.com/2020/09/21/manufacturing-test-fixtures/",
                    ),
                    ResourcePlan(
                        title="Boundary scan tutorial",
                        type="video",
                        notes="Automate JTAG tests",
                        url="https://www.youtube.com/watch?v=6YfY8K4D4x0",
                    ),
                    ResourcePlan(
                        title="SparkFun DFM checklist",
                        type="guide",
                        notes="Review before CM handoff",
                        url="https://learn.sparkfun.com/tutorials/design-for-manufacturability/all",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 35 – Hardware design validation & compliance",
                tasks=[
                    TaskPlan(
                        title="Schematic review blitz",
                        description=(
                            "Run structured schematic review, cross-check"
                            " net classes, power, and decoupling."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Inspect schematic snippets; suggest redundancy"
                            " or protection additions."
                        ),
                    ),
                    TaskPlan(
                        title="PCB layout validation",
                        description=(
                            "Use Altium/KiCad DRC, impedance calculators,"
                            " and stackup analysis."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review layout heatmaps; highlight EMI hotspots"
                            " and return path issues."
                        ),
                    ),
                    TaskPlan(
                        title="Compliance gap analysis",
                        description=(
                            "Prepare for FCC/CE by reviewing emissions,"
                            " immunity, and safety requirements."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Evaluate compliance plan; suggest pre-scan"
                            " strategies."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Altium design review checklist",
                        type="checklist",
                        notes="Schematic & PCB review",
                        url="https://resources.altium.com/p/design-review-checklist",
                    ),
                    ResourcePlan(
                        title="Keysight impedance control guide",
                        type="guide",
                        notes="Transmission line refresher",
                        url="https://www.keysight.com/us/en/assets/7018-04278/brochures/5991-2176EN.pdf",
                    ),
                    ResourcePlan(
                        title="Pre-compliance testing tips",
                        type="article",
                        notes="Plan lab sessions",
                        url="https://www.edn.com/pre-compliance-testing-tips/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 36 – Reliability engineering & environmental tests",
                tasks=[
                    TaskPlan(
                        title="HALT/HASS planning",
                        description=(
                            "Design Highly Accelerated Life Tests, define"
                            " stress profiles, and instrumentation."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review HALT plan; ensure coverage of key failure"
                            " modes."
                        ),
                    ),
                    TaskPlan(
                        title="Environmental testing",
                        description=(
                            "Conduct thermal cycling, humidity, and vibration"
                            " tests with logging."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Interpret environmental test results; propose"
                            " design tweaks."
                        ),
                    ),
                    TaskPlan(
                        title="Reliability statistics",
                        description=(
                            "Compute MTBF/MTTF using Weibull analysis from"
                            " accelerated data."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review Weibull curve fits; challenge assumptions"
                            " and extrapolations."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="HALT/HASS fundamentals",
                        type="article",
                        notes="Stress planning",
                        url="https://www.weibull.com/hotwire/issue21/relbasics21.htm",
                    ),
                    ResourcePlan(
                        title="NI environmental testing primer",
                        type="article",
                        notes="Instrumentation guidance",
                        url="https://www.ni.com/en/innovations/white-papers/08/environmental-test.html",
                    ),
                    ResourcePlan(
                        title="Weibull analysis tutorial",
                        type="guide",
                        notes="Reliability statistics",
                        url="https://www.weibull.com/basics/statistics.htm",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 37 – Supply chain resilience & lifecycle management",
                tasks=[
                    TaskPlan(
                        title="Component risk assessment",
                        description=(
                            "Analyze BOM for lifecycle, availability, and"
                            " compliance issues."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review BOM risk matrix; propose alternates for"
                            " high-risk parts."
                        ),
                    ),
                    TaskPlan(
                        title="Lifecycle management playbook",
                        description=(
                            "Define change control, PCN handling, and inventory"
                            " strategy."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Evaluate lifecycle plan; suggest automation for"
                            " PCN monitoring."
                        ),
                    ),
                    TaskPlan(
                        title="Manufacturing data flows",
                        description=(
                            "Establish traceability linking serial numbers,"
                            " calibration data, and firmware versions."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review traceability schema; recommend retention"
                            " policies."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="SiliconExpert overview",
                        type="guide",
                        notes="Monitor component health",
                        url="https://www.siliconexpert.com/solutions/",
                    ),
                    ResourcePlan(
                        title="IPC-1754 supply chain data standard",
                        type="standard",
                        notes="Traceability reference",
                        url="https://www.ipc.org/ipc-1754",
                    ),
                    ResourcePlan(
                        title="Manufacturing traceability best practices",
                        type="article",
                        notes="Serialization approaches",
                        url="https://www.assemblymag.com/articles/94737-best-practices-for-creating-product-traceability",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 38 – Regulatory compliance & certification prep",
                tasks=[
                    TaskPlan(
                        title="Regulatory landscape mapping",
                        description=(
                            "Identify applicable standards (FCC, CE, UL,"
                            " RoHS) and documentation needs."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review regulatory map; highlight missing regions"
                            " or product classes."
                        ),
                    ),
                    TaskPlan(
                        title="Technical file compilation",
                        description=(
                            "Assemble test reports, schematics, risk analyses,"
                            " and user manuals."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Audit technical file index; suggest improvements"
                            " for notified body review."
                        ),
                    ),
                    TaskPlan(
                        title="Pre-certification lab coordination",
                        description=(
                            "Schedule lab sessions, prepare samples, and"
                            " develop issue triage plan."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Evaluate lab prep plan; ensure fallback if tests"
                            " fail."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="CE marking roadmap",
                        type="guide",
                        notes="EU compliance steps",
                        url="https://ec.europa.eu/growth/single-market/ce-marking/",
                    ),
                    ResourcePlan(
                        title="UL certification overview",
                        type="article",
                        notes="Testing preparation",
                        url="https://www.ul.com/resources/getting-started-ul-certification",
                    ),
                    ResourcePlan(
                        title="RoHS/REACH compliance checklist",
                        type="checklist",
                        notes="Materials documentation",
                        url="https://www.rohsguide.com/rohs-compliance.htm",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 39 – Phase integration, storytelling, and demo",
                tasks=[
                    TaskPlan(
                        title="Intelligent firmware showcase",
                        description=(
                            "Prepare interactive demo highlighting ML, safety,"
                            " and diagnostics capabilities."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Refine demo storyline; align with hiring manager"
                            " priorities."
                        ),
                    ),
                    TaskPlan(
                        title="Certification dossier review",
                        description=(
                            "Peer-review compliance docs, ensure version"
                            " control and sign-off readiness."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Audit dossier; find sections lacking evidence."
                        ),
                    ),
                    TaskPlan(
                        title="Phase retrospective & backlog refresh",
                        description=(
                            "Conduct retro, update risk register, and refine"
                            " product roadmap for final phase."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Summarize retro; highlight actions feeding into"
                            " Phase 4 launch."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Technical demo storytelling workshop",
                        type="course",
                        notes="Sharpen presentation",
                        url="https://www.udemy.com/course/tech-presentation-storytelling/",
                    ),
                    ResourcePlan(
                        title="Compliance documentation best practices",
                        type="article",
                        notes="Organize evidence",
                        url="https://www2.deloitte.com/us/en/pages/risk/articles/project-compliance-documentation.html",
                    ),
                    ResourcePlan(
                        title="Retrospective facilitation guide",
                        type="article",
                        notes="Keep retro focused",
                        url="https://www.mountaingoatsoftware.com/agile/scrum/sprint-retrospective",
                    ),
                ],
            ),
        ],
    ),
    PhasePlan(
        name="Phase 4 – Productization, Launch & Career Amplification",
        description=(
            "Polish the product experience, finalize launch readiness, and"
            " translate achievements into standout portfolio assets."
            " Concludes with simulated launch, community contributions,"
            " and career outreach campaign."
        ),
        weeks=[
            WeekPlan(
                focus="Week 40 – Productization roadmap & customer empathy",
                tasks=[
                    TaskPlan(
                        title="Voice-of-customer synthesis",
                        description=(
                            "Interview target users, synthesize personas,"
                            " and update product requirements."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Summarize interview transcripts; highlight latent"
                            " needs influencing roadmap."
                        ),
                    ),
                    TaskPlan(
                        title="Productization backlog grooming",
                        description=(
                            "Prioritize refinement backlog, define acceptance"
                            " criteria, and map to sprints."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review backlog; suggest scope cuts or deferrals"
                            " to hit launch."
                        ),
                    ),
                    TaskPlan(
                        title="Experience journey mapping",
                        description=(
                            "Create end-to-end journey map from unboxing to"
                            " data insights with friction points."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Inspect journey map; recommend delight moments"
                            " and instrumentation."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Interview synthesis template",
                        type="template",
                        notes="Notion board",
                        url="https://www.notion.so/templates/user-interview-board",
                    ),
                    ResourcePlan(
                        title="Roman Pichler backlog guide",
                        type="article",
                        notes="Product backlog tips",
                        url="https://www.romanpichler.com/blog/",
                    ),
                    ResourcePlan(
                        title="Service design blueprint primer",
                        type="article",
                        notes="Journey mapping",
                        url="https://www.nngroup.com/articles/service-blueprints-definition/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 41 – UX refinement & embedded UI polish",
                tasks=[
                    TaskPlan(
                        title="Qt/Qt Quick HMI enhancements",
                        description=(
                            "Refine embedded UI layouts, accessibility, and"
                            " localization pipeline."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review UI mocks; suggest improvements for"
                            " readability under glare."
                        ),
                    ),
                    TaskPlan(
                        title="UX validation",
                        description=(
                            "Conduct usability tests, capture heatmaps, and"
                            " iterate on pain points."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Analyze usability findings; propose prioritized"
                            " fixes."
                        ),
                    ),
                    TaskPlan(
                        title="UI performance optimization",
                        description=(
                            "Profile rendering pipeline, GPU utilization,"
                            " and reduce frame drops."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Inspect profiler output; suggest caching or"
                            " shader optimizations."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Qt for MCUs best practices",
                        type="docs",
                        notes="Optimize resource usage",
                        url="https://doc.qt.io/qtformcu/",
                    ),
                    ResourcePlan(
                        title="NNGroup usability testing 101",
                        type="guide",
                        notes="Run efficient tests",
                        url="https://www.nngroup.com/articles/usability-testing-101/",
                    ),
                    ResourcePlan(
                        title="Embedded GPU profiling techniques",
                        type="article",
                        notes="Performance tuning",
                        url="https://developer.nvidia.com/blog/profiling-embedded-gpus/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 42 – Data analytics & insight delivery",
                tasks=[
                    TaskPlan(
                        title="Analytics pipeline validation",
                        description=(
                            "Ensure edge-to-cloud data fidelity, schema"
                            " evolution, and governance."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Audit analytics pipeline; point out data quality"
                            " risks."
                        ),
                    ),
                    TaskPlan(
                        title="Insight dashboards",
                        description=(
                            "Build Grafana/Metabase dashboards with actionable"
                            " KPIs for ops teams."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review dashboard layouts; suggest metric cadence"
                            " and alerts."
                        ),
                    ),
                    TaskPlan(
                        title="Data storytelling",
                        description=(
                            "Craft narratives translating telemetry into"
                            " product decisions for stakeholders."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Edit analytics narrative; highlight business"
                            " outcomes."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Metabase modeling guide",
                        type="docs",
                        notes="Dashboard fundamentals",
                        url="https://www.metabase.com/docs/latest/",
                    ),
                    ResourcePlan(
                        title="Data storytelling for engineers",
                        type="course",
                        notes="Communicate insights",
                        url="https://www.coursera.org/learn/analytics-storytelling",
                    ),
                    ResourcePlan(
                        title="Grafana alerting walkthrough",
                        type="video",
                        notes="Set up actionable alerts",
                        url="https://grafana.com/go/learn/alerting/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 43 – Production logistics & operations runbooks",
                tasks=[
                    TaskPlan(
                        title="Operations runbook",
                        description=(
                            "Document on-call procedures, escalation paths,"
                            " and service-level objectives."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review runbook; ensure actionable steps and"
                            " clear ownership."
                        ),
                    ),
                    TaskPlan(
                        title="Fulfillment & logistics mapping",
                        description=(
                            "Plan packaging, shipping, RMA workflows, and"
                            " service tooling."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Assess logistics plan; flag bottlenecks or"
                            " compliance concerns."
                        ),
                    ),
                    TaskPlan(
                        title="Support tooling setup",
                        description=(
                            "Integrate helpdesk, knowledge base, and telemetry"
                            " insights for support agents."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Evaluate support stack; suggest automations and"
                            " feedback loops."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="SRE workbook",
                        type="book",
                        notes="On-call excellence",
                        url="https://sre.google/workbook/",
                    ),
                    ResourcePlan(
                        title="RMA process best practices",
                        type="article",
                        notes="Reduce turnaround",
                        url="https://www.ifixit.com/News/58034/how-to-build-a-bulletproof-rma-process",
                    ),
                    ResourcePlan(
                        title="Zendesk knowledge base playbook",
                        type="guide",
                        notes="Support tooling",
                        url="https://support.zendesk.com/hc/en-us/articles/360022184994",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 44 – Performance scaling & cost optimization",
                tasks=[
                    TaskPlan(
                        title="Performance budget enforcement",
                        description=(
                            "Define budgets for latency, memory, and network"
                            " usage; add CI checks."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review performance budget thresholds; align with"
                            " product requirements."
                        ),
                    ),
                    TaskPlan(
                        title="Cost modeling",
                        description=(
                            "Model unit economics, cloud costs, support"
                            " staffing, and BOM sensitivity."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Inspect cost model; stress test assumptions for"
                            " scaling."
                        ),
                    ),
                    TaskPlan(
                        title="Performance tuning sprint",
                        description=(
                            "Execute targeted optimizations (cache, RTC"
                            " scheduling, payload batching)."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Prioritize tuning backlog; estimate ROI per"
                            " optimization."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Embedded performance budget guide",
                        type="article",
                        notes="Budget templates",
                        url="https://interrupt.memfault.com/blog/performance-budgets",
                    ),
                    ResourcePlan(
                        title="AWS IoT cost optimization",
                        type="guide",
                        notes="Cloud cost levers",
                        url="https://aws.amazon.com/solutions/cost-optimization/",
                    ),
                    ResourcePlan(
                        title="Latency optimization playbook",
                        type="talk",
                        notes="Tuning inspiration",
                        url="https://www.youtube.com/watch?v=7V5d0K8XJ7A",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 45 – Security audits & red team drills",
                tasks=[
                    TaskPlan(
                        title="Security audit walkthrough",
                        description=(
                            "Perform internal audit vs. OWASP ISVS, capture"
                            " residual risks and mitigations."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Review audit findings; prioritize remediation"
                            " backlog."
                        ),
                    ),
                    TaskPlan(
                        title="Red team exercise",
                        description=(
                            "Simulate adversarial scenarios (firmware tamper,"
                            " credential theft) and practice response."
                        ),
                        estimated_hours=4.5,
                        ai_prompt=(
                            "Analyze red team reports; suggest stronger"
                            " detection signals."
                        ),
                    ),
                    TaskPlan(
                        title="Update security training",
                        description=(
                            "Refresh secure coding guidelines, run lunch-and-"
                            "learn for stakeholders."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Review training slides; ensure relevance to"
                            " firmware engineers."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="OWASP ISVS checklist",
                        type="standard",
                        notes="Audit baseline",
                        url="https://owasp.org/www-project-iot-security-verification-standard/",
                    ),
                    ResourcePlan(
                        title="Red team playbook",
                        type="article",
                        notes="Simulation guidance",
                        url="https://www.paloaltonetworks.com/cyberpedia/what-is-red-teaming",
                    ),
                    ResourcePlan(
                        title="Secure coding lunch-and-learn kit",
                        type="template",
                        notes="Training materials",
                        url="https://github.com/OWASP/DevSecOpsGuideline",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 46 – Release management & documentation freeze",
                tasks=[
                    TaskPlan(
                        title="Release checklist completion",
                        description=(
                            "Finalize release checklist, approvals, and"
                            " sign-off artifacts."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review release checklist; ensure regulatory"
                            " compliance steps."
                        ),
                    ),
                    TaskPlan(
                        title="Documentation freeze",
                        description=(
                            "Lock documentation versions, archive release"
                            " packages, and tag repos."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Ensure doc freeze covers translations, support"
                            " articles, and release notes."
                        ),
                    ),
                    TaskPlan(
                        title="Training & enablement",
                        description=(
                            "Deliver training webinars for support, sales,"
                            " and partners."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Review webinar deck; align messaging with value"
                            " propositions."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Release readiness checklist",
                        type="checklist",
                        notes="Ensure completeness",
                        url="https://www.productplan.com/glossary/release-readiness-review/",
                    ),
                    ResourcePlan(
                        title="Microsoft style guide",
                        type="guide",
                        notes="Consistency before freeze",
                        url="https://learn.microsoft.com/style-guide/",
                    ),
                    ResourcePlan(
                        title="Enablement plan template",
                        type="template",
                        notes="Train stakeholders",
                        url="https://miro.com/miroverse/sales-enablement-plan/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 47 – Launch simulation & incident readiness",
                tasks=[
                    TaskPlan(
                        title="Game day exercise",
                        description=(
                            "Run launch-day simulation with staged incidents"
                            " (telemetry spike, failed updates)."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review game day results; strengthen response"
                            " playbooks."
                        ),
                    ),
                    TaskPlan(
                        title="Incident command training",
                        description=(
                            "Establish incident commander rotation and comms"
                            " templates."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Evaluate incident comms templates; ensure clarity"
                            " under pressure."
                        ),
                    ),
                    TaskPlan(
                        title="Post-launch metrics",
                        description=(
                            "Define success metrics, monitoring thresholds,"
                            " and reporting cadence."
                        ),
                        estimated_hours=3.0,
                        ai_prompt=(
                            "Review metrics plan; align with exec updates."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="AWS game day handbook",
                        type="guide",
                        notes="Exercise ideas",
                        url="https://aws.amazon.com/gameday/",
                    ),
                    ResourcePlan(
                        title="Incident command system for tech",
                        type="article",
                        notes="ICS adaptation",
                        url="https://www.usenix.org/conference/srecon19emea/presentation/murphy",
                    ),
                    ResourcePlan(
                        title="DORA metrics primer",
                        type="guide",
                        notes="Key KPIs",
                        url="https://www.devops-research.com/research.html",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 48 – Portfolio refresh & storytelling",
                tasks=[
                    TaskPlan(
                        title="Portfolio rebuild",
                        description=(
                            "Update personal site with case studies, demos,"
                            " and technical deep dives."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review portfolio layout; highlight sections to"
                            " elevate credibility."
                        ),
                    ),
                    TaskPlan(
                        title="Highlight reel production",
                        description=(
                            "Record 3-minute video summarizing project impact"
                            " and metrics."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Refine video script; emphasize outcomes and"
                            " leadership."
                        ),
                    ),
                    TaskPlan(
                        title="Reference packet",
                        description=(
                            "Compile reference letters, testimonials, and"
                            " performance metrics."
                        ),
                        estimated_hours=3.0,
                        ai_prompt=(
                            "Review reference packet; ensure narratives align"
                            " with target roles."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Engineering portfolio checklist",
                        type="article",
                        notes="Ensure completeness",
                        url="https://www.freecodecamp.org/news/how-to-build-a-strong-engineering-portfolio/",
                    ),
                    ResourcePlan(
                        title="Loom storytelling tips",
                        type="video",
                        notes="Record engaging clips",
                        url="https://www.loom.com/blog/how-to-make-engaging-videos",
                    ),
                    ResourcePlan(
                        title="Reference letter template",
                        type="template",
                        notes="Consistent requests",
                        url="https://www.indeed.com/career-advice/career-development/reference-letter-template",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 49 – Interview prep & coding drills",
                tasks=[
                    TaskPlan(
                        title="Systems design interview prep",
                        description=(
                            "Practice embedded systems design prompts, capture"
                            " frameworks and diagrams."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Mock interview me on real-time systems; provide"
                            " scoring rubric."
                        ),
                    ),
                    TaskPlan(
                        title="Firmware coding kata",
                        description=(
                            "Run timed coding drills (bit manipulation, state"
                            " machines) with code review."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Generate new embedded coding challenges and"
                            " evaluate my solutions."
                        ),
                    ),
                    TaskPlan(
                        title="Behavioral interview stories",
                        description=(
                            "Refine STAR stories tied to roadmap achievements"
                            " and leadership."
                        ),
                        estimated_hours=3.0,
                        ai_prompt=(
                            "Review STAR stories; suggest quantified impacts"
                            " and tighter endings."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Embedded systems interview questions repo",
                        type="repo",
                        notes="Practice prompts",
                        url="https://github.com/randrew/embedded-systems-interview-questions",
                    ),
                    ResourcePlan(
                        title="Interviewing.io firmware sessions",
                        type="platform",
                        notes="Mock interviews",
                        url="https://interviewing.io/",
                    ),
                    ResourcePlan(
                        title="STAR storytelling workbook",
                        type="worksheet",
                        notes="Craft narratives",
                        url="https://careerservices.upenn.edu/resources/the-star-method/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 50 – Community impact & open-source contributions",
                tasks=[
                    TaskPlan(
                        title="Open-source contribution sprint",
                        description=(
                            "Contribute to Zephyr/PlatformIO/TFLM with"
                            " meaningful PR and documentation."
                        ),
                        estimated_hours=4.0,
                        ai_prompt=(
                            "Review contribution draft; ensure alignment with"
                            " project guidelines."
                        ),
                    ),
                    TaskPlan(
                        title="Community talk or blog",
                        description=(
                            "Prepare conference talk abstract or detailed"
                            " blog post."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Edit talk abstract; highlight unique insights."
                        ),
                    ),
                    TaskPlan(
                        title="Mentorship & outreach",
                        description=(
                            "Host office hours or mentorship sessions for"
                            " early-career engineers."
                        ),
                        estimated_hours=3.0,
                        ai_prompt=(
                            "Suggest mentorship topics and resources to share."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Zephyr contributing guide",
                        type="docs",
                        notes="Follow PR etiquette",
                        url="https://docs.zephyrproject.org/latest/contribute/index.html",
                    ),
                    ResourcePlan(
                        title="Write the Docs talk tips",
                        type="article",
                        notes="Talk preparation",
                        url="https://www.writethedocs.org/conf/",
                    ),
                    ResourcePlan(
                        title="Open source leadership guide",
                        type="guide",
                        notes="Structure mentorship",
                        url="https://opensource.guide/leadership-and-governance/",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 51 – Capstone hardening & final demo",
                tasks=[
                    TaskPlan(
                        title="Capstone polish sprint",
                        description=(
                            "Resolve final bugs, polish documentation, and"
                            " ensure tests are green."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Review bug list; prioritize final fixes against"
                            " launch goals."
                        ),
                    ),
                    TaskPlan(
                        title="Final live demo rehearsal",
                        description=(
                            "Dry-run final demo with mentors, capture feedback,"
                            " and refine flow."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Play role of skeptical stakeholder; stress-test"
                            " my demo messaging."
                        ),
                    ),
                    TaskPlan(
                        title="Celebration & gratitude",
                        description=(
                            "Plan recognition for collaborators and supporters,"
                            " share wins publicly."
                        ),
                        estimated_hours=2.5,
                        ai_prompt=(
                            "Draft gratitude notes; ensure sincerity and"
                            " specificity."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Final demo checklist",
                        type="checklist",
                        notes="No surprises",
                        url="https://www.atlassian.com/team-playbook/plays/demo",
                    ),
                    ResourcePlan(
                        title="Retrospective celebration ideas",
                        type="article",
                        notes="Mark the milestone",
                        url="https://www.atlassian.com/agile/teamwork/team-celebrations",
                    ),
                    ResourcePlan(
                        title="Gratitude writing guide",
                        type="guide",
                        notes="Thoughtful thank-yous",
                        url="https://www.mindtools.com/ak7b7ea/how-to-write-a-thank-you-letter",
                    ),
                ],
            ),
            WeekPlan(
                focus="Week 52 – Launch retrospective & career outreach",
                tasks=[
                    TaskPlan(
                        title="Launch retrospective",
                        description=(
                            "Conduct final retro, document lessons, and update"
                            " risk register for sustainability."
                        ),
                        estimated_hours=3.0,
                        ai_prompt=(
                            "Summarize retro themes; recommend habits to"
                            " maintain momentum."
                        ),
                    ),
                    TaskPlan(
                        title="Career outreach campaign",
                        description=(
                            "Execute targeted outreach to hiring managers,"
                            " alumni, and mentors with tailored packets."
                        ),
                        estimated_hours=3.5,
                        ai_prompt=(
                            "Review outreach emails; personalize messaging per"
                            " recipient."
                        ),
                    ),
                    TaskPlan(
                        title="Roadmap transition plan",
                        description=(
                            "Define next-quarter goals, maintenance routines,"
                            " and learning backlog."
                        ),
                        estimated_hours=3.0,
                        ai_prompt=(
                            "Evaluate transition plan; suggest focus areas for"
                            " continued mastery."
                        ),
                    ),
                ],
                resources=[
                    ResourcePlan(
                        title="Networking outreach templates",
                        type="article",
                        notes="Tailor messages",
                        url="https://www.themuse.com/advice/networking-email-templates",
                    ),
                    ResourcePlan(
                        title="Career-focused retro template",
                        type="worksheet",
                        notes="Guide reflection",
                        url="https://www.notion.so/templates/career-retro",
                    ),
                    ResourcePlan(
                        title="Continuous learning plan guide",
                        type="article",
                        notes="Plan next steps",
                        url="https://hbr.org/2021/03/how-to-build-a-learning-culture",
                    ),
                ],
            ),
        ],
        projects=[
            ProjectPlan(
                name="Productization UX Polish",
                description=(
                    " Qt/PySide6 HMI refresh with accessibility, dark-mode,"
                    " and localisation toggles aligned to Samsung 32\" panel"
                    " constraints."
                ),
                start_week=40,
                end_week=44,
                status="planned",
                repo_url="https://github.com/khashyap0803/productization-ux",
            ),
            ProjectPlan(
                name="Intelligence & Analytics Console",
                description=(
                    "Grafana/Metabase bundle streaming TinyML + ops"
                    " metrics with alerting hooks for Bosch/TI interview"
                    " demos."
                ),
                start_week=42,
                end_week=47,
                status="planned",
                repo_url="https://github.com/khashyap0803/embedded-analytics-console",
            ),
            ProjectPlan(
                name="Career Brand Launchpad",
                description=(
                    "Portfolio rebuild, Loom highlight reel, and GitHub"
                    " Pages microsite showcasing 15 projects + 4 certs."
                ),
                start_week=45,
                end_week=52,
                status="planned",
                repo_url="https://github.com/khashyap0803/career-brand",
                demo_url="https://embedded-mastery-khashyap.github.io",
            ),
        ],
        certifications=[
            CertificationPlan(
                name="AWS IoT Specialty",
                provider="AWS Training & Certification",
                due_week=48,
                status="planned",
                progress=0.0,
            ),
        ],
        metrics=[
            MetricPlan(
                metric_type="ux_test_nps",
                value=68.0,
                unit="nps",
                week_number=45,
            ),
            MetricPlan(
                metric_type="job_applications_dispatched",
                value=50.0,
                unit="count",
                week_number=52,
            ),
        ],
    ),
]
GLOBAL_PROJECT_PLANS: List[ProjectPlan] = []
GLOBAL_CERTIFICATION_PLANS: List[CertificationPlan] = []
GLOBAL_METRIC_PLANS: List[MetricPlan] = []
APPLICATION_PLANS: List[ApplicationPlan] = [
    ApplicationPlan(
        company="Bosch India",
        role="Senior Embedded Engineer",
        status="draft",
        week_number=26,
        source="Naukri",
        next_action="Finalize Zephyr mission computer write-up for batch #1 submissions (10 companies).",
        notes="Target ₹15-18 LPA; aligns with 50-application OKR.",
    ),
    ApplicationPlan(
        company="Texas Instruments",
        role="Firmware Engineer",
        status="draft",
        week_number=27,
        source="LinkedIn",
        next_action="Record TinyML demo clip tailored to TI automotive group.",
        notes="Part of referral cohort via alumni; counts toward 50 target.",
    ),
    ApplicationPlan(
        company="Tata Elxsi",
        role="Lead IoT Developer",
        status="draft",
        week_number=28,
        source="Company Careers",
        next_action="Ship OTA/fleet ops case study PDF and prepare HR intro.",
        notes="Batch #2 of 5 targeted design consultancies.",
    ),
    ApplicationPlan(
        company="Continental Automotive",
        role="Embedded Safety Engineer",
        status="draft",
        week_number=29,
        source="Naukri",
        next_action="Highlight ASIL-B safety manager metrics in cover letter.",
        notes="Focus on ISO 26262 readiness; part of 50-app log.",
    ),
    ApplicationPlan(
        company="Qualcomm Hyderabad",
        role="Senior Firmware Engineer",
        status="draft",
        week_number=30,
        source="LinkedIn",
        next_action="Benchmark throughput numbers on Ryzen rig for RF-heavy resume bullet.",
        notes="Batch #3 (SoC vendors) – 8 submissions planned.",
    ),
    ApplicationPlan(
        company="Ola Electric",
        role="IoT Platform Lead",
        status="draft",
        week_number=31,
        source="Referral",
        next_action="Schedule mock interview to stress-test fleet ops story.",
        notes="Supports ₹20L+ target roles; includes 5 allied startups.",
    ),
    ApplicationPlan(
        company="NVIDIA Embedded",
        role="Edge AI Engineer",
        status="draft",
        week_number=32,
        source="LinkedIn",
        next_action="Publish RTX 5060 Ti CUDA TinyML benchmark blog before applying.",
        notes="Batch #4 (AI heavy) – ensures PC max-out narrative.",
    ),
    ApplicationPlan(
        company="Bosch Global Software",
        role="IoT Developer",
        status="draft",
        week_number=33,
        source="Hackster.io",
        next_action="Share community talk + open-source contribution links for follow-up.",
        notes="Represents second wave of Bosch applications; keeps 50-app cadence warm.",
    ),
]


def _build_segments(tasks: Iterable[TaskPlan]) -> List[dict]:
    segments: List[dict] = []
    next_hour_number = 1
    for plan in tasks:
        total_minutes = max(int(round(plan.estimated_hours * 60)), MIN_SEGMENT_MINUTES)
        segment_count = max(1, round(total_minutes / 60))
        base_minutes = total_minutes // segment_count
        remainder = total_minutes % segment_count
        for index in range(segment_count):
            minutes = base_minutes + (1 if index < remainder else 0)
            minutes = max(minutes, MIN_SEGMENT_MINUTES)
            segments.append(
                {
                    "hour_number": next_hour_number,
                    "title": plan.title
                    if segment_count == 1
                    else f"{plan.title} (Segment {index + 1}/{segment_count})",
                    "description": plan.description,
                    "estimated_minutes": minutes,
                    "status": plan.status,
                    "ai_prompt": plan.ai_prompt,
                    "source_task_title": plan.title,
                }
            )
            next_hour_number += 1
    return segments


def _compose_working_day(index: int, week_start: date, segments: List[dict]) -> dict:
    scheduled = week_start + timedelta(days=index)
    titles: List[str] = []
    seen: set[str] = set()
    for segment in segments:
        title = segment["source_task_title"]
        if title not in seen:
            seen.add(title)
            titles.append(title)
    notes = f"Focus: {', '.join(titles)}" if titles else None
    return {
        "number": index + 1,
        "scheduled_date": scheduled.isoformat(),
        "focus": titles[0] if titles else "Focused execution",
        "notes": notes,
        "status": "pending",
        "hours": [
            {
                "hour_number": item["hour_number"],
                "title": item["title"],
                "description": item.get("description"),
                "estimated_minutes": item["estimated_minutes"],
                "status": item.get("status", "pending"),
                "ai_prompt": item.get("ai_prompt"),
                "source_task_title": item["source_task_title"],
            }
            for item in segments
        ],
    }


def _compose_integration_day(week_start: date, hour_number: int) -> dict:
    scheduled = week_start + timedelta(days=5)
    return {
        "number": 6,
        "scheduled_date": scheduled.isoformat(),
        "focus": "Integration, reflection, portfolio updates",
        "notes": "Consolidate notes, update demos, plan next sprint.",
        "status": "pending",
        "hours": [
            {
                "hour_number": hour_number,
                "title": "Weekly integration & portfolio review",
                "description": "Summarize lessons, sync repos, publish status update.",
                "estimated_minutes": INTEGRATION_MINUTES,
                "status": "pending",
                "ai_prompt": REVISION_PROMPT,
                "source_task_title": "Weekly reflection",
            }
        ],
    }


def _compose_rest_day(week_start: date) -> dict:
    scheduled = week_start + timedelta(days=6)
    return {
        "number": 7,
        "scheduled_date": scheduled.isoformat(),
        "focus": "Rest & recharge",
        "notes": "No scheduled work. Prioritize health, family, and hobbies.",
        "status": "pending",
        "hours": [],
    }


def _build_days(tasks: Iterable[TaskPlan], week_start: date) -> List[dict]:
    segments = _build_segments(tasks)
    days: List[dict] = []
    day_segments: List[dict] = []
    minutes_accumulated = 0
    work_day_index = 0

    for segment in segments:
        if work_day_index >= 5:
            day_segments.append(segment)
            continue
        will_overflow = minutes_accumulated + segment["estimated_minutes"] > MINUTES_PER_DAY
        if will_overflow and day_segments:
            days.append(_compose_working_day(work_day_index, week_start, day_segments))
            work_day_index += 1
            day_segments = []
            minutes_accumulated = 0
        day_segments.append(segment)
        minutes_accumulated += segment["estimated_minutes"]

    if day_segments and work_day_index < 5:
        days.append(_compose_working_day(work_day_index, week_start, day_segments))
        work_day_index += 1

    while work_day_index < 5:
        placeholder = {
            "hour_number": segments[-1]["hour_number"] + 1 if segments else work_day_index + 1,
            "title": "Deep work focus block",
            "description": "Allocate time for deliberate practice or backlog grooming.",
            "estimated_minutes": MIN_SEGMENT_MINUTES,
            "status": "pending",
            "ai_prompt": "Identify one micro-skill to sharpen today and craft an AI-assisted plan.",
            "source_task_title": "Deep work",
        }
        segments.append(placeholder)
        days.append(_compose_working_day(work_day_index, week_start, [placeholder]))
        work_day_index += 1

    integration_start = segments[-1]["hour_number"] + 1 if segments else 1
    days.append(_compose_integration_day(week_start, integration_start))
    days.append(_compose_rest_day(week_start))
    return days


def build_seed() -> dict:
    seed: dict = {"phases": []}
    week_counter = 0
    for phase in PHASES:
        phase_start = START_DATE + timedelta(weeks=week_counter)
        phase_end = phase_start + timedelta(weeks=len(phase.weeks)) - timedelta(days=1)
        phase_entry = {
            "name": phase.name,
            "description": phase.description,
            "start_date": phase_start.isoformat(),
            "end_date": phase_end.isoformat(),
            "weeks": [],
        }
        for week_plan in phase.weeks:
            week_counter += 1
            week_start = START_DATE + timedelta(weeks=week_counter - 1)
            week_entry = {
                "number": week_counter,
                "start_date": week_start.isoformat(),
                "end_date": (week_start + timedelta(days=6)).isoformat(),
                "focus": week_plan.focus,
                "tasks": [
                    {
                        "title": task.title,
                        "description": task.description,
                        "estimated_hours": task.estimated_hours,
                        "status": task.status,
                        "ai_prompt": task.ai_prompt,
                    }
                    for task in week_plan.tasks
                ],
                "resources": [
                    {
                        "title": resource.title,
                        "type": resource.type,
                        "notes": resource.notes,
                        "url": resource.url,
                    }
                    for resource in week_plan.resources
                ],
            }
            week_entry["days"] = _build_days(week_plan.tasks, week_start)
            phase_entry["weeks"].append(week_entry)
        if phase.projects:
            phase_entry["projects"] = [_project_payload(plan) for plan in phase.projects]
        if phase.certifications:
            phase_entry["certifications"] = [
                _certification_payload(plan) for plan in phase.certifications
            ]
        if phase.metrics:
            phase_entry["metrics"] = [_metric_payload(plan) for plan in phase.metrics]
        seed["phases"].append(phase_entry)

    seed["projects"] = [_project_payload(plan) for plan in GLOBAL_PROJECT_PLANS]
    seed["certifications"] = [
        _certification_payload(plan) for plan in GLOBAL_CERTIFICATION_PLANS
    ]
    seed["metrics"] = [_metric_payload(plan) for plan in GLOBAL_METRIC_PLANS]
    seed["applications"] = [_application_payload(plan) for plan in APPLICATION_PLANS]

    if week_counter != 52:
        raise ValueError(f"Expected 52 weeks, generated {week_counter}")
    return seed


def main() -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    seed_path = data_dir / "roadmap_seed.json"
    seed_path.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {seed_path}")


if __name__ == "__main__":
    main()
