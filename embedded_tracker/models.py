"""Database models representing the embedded systems roadmap domain."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SAEnum, Index
from sqlmodel import Field, SQLModel

from .utils import utcnow as _utcnow


class TaskStatus(str, Enum):
    """Lifecycle states for work items tracked in the roadmap."""

    PENDING = "pending"
    WORKING = "working"
    BREAK = "break"
    PAUSED = "paused"
    COMPLETED = "completed"


TASK_STATUS_ENUM = SAEnum(
    TaskStatus,
    name="task_status_v2",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    native_enum=False,
    validate_strings=True,
)


class Phase(SQLModel, table=True):
    """High-level period such as Phase 1: Foundations."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    start_date: Optional[date] = None  # Dynamic: set when phase starts
    end_date: Optional[date] = None  # Dynamic: set when phase ends
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(
            TASK_STATUS_ENUM.copy(),
            nullable=False,
            index=True,
        ),
    )
    actual_start: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    actual_end: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )



class Week(SQLModel, table=True):
    """Week within a phase, holding a collection of tasks and milestones."""

    id: Optional[int] = Field(default=None, primary_key=True)
    number: int = Field(index=True)
    start_date: Optional[date] = None  # Dynamic: set when week starts
    end_date: Optional[date] = None  # Dynamic: set when week ends
    focus: Optional[str] = None
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(
            TASK_STATUS_ENUM.copy(),
            nullable=False,
            index=True,
        ),
    )
    actual_start: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    actual_end: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    phase_id: int = Field(foreign_key="phase.id")


class DayPlan(SQLModel, table=True):
    """Day-level schedule item nested under a week."""

    id: Optional[int] = Field(default=None, primary_key=True)
    number: int = Field(index=True)
    scheduled_date: Optional[date] = None  # Dynamic: set when day starts
    focus: Optional[str] = None
    notes: Optional[str] = None
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(
            TASK_STATUS_ENUM.copy(),
            nullable=False,
            index=True,
        ),
    )
    actual_start: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    actual_end: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    week_id: int = Field(foreign_key="week.id")


class Task(SQLModel, table=True):
    """Atomic hour-level unit of work aligned to the roadmap."""

    # Composite indices for common query patterns (performance optimization)
    __table_args__ = (
        Index('idx_task_week_status', 'week_id', 'status'),
        Index('idx_task_week_day', 'week_id', 'day_id'),
        Index('idx_task_day_hour', 'day_id', 'hour_number'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(
            TASK_STATUS_ENUM.copy(),
            nullable=False,
            index=True,
        ),
    )
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    ai_prompt: Optional[str] = None
    hour_number: Optional[int] = Field(default=None, index=True)
    status_updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    first_started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    last_work_started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    last_break_started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    last_pause_started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    total_work_seconds: int = Field(default=0, ge=0)
    total_break_seconds: int = Field(default=0, ge=0)
    total_pause_seconds: int = Field(default=0, ge=0)

    week_id: int = Field(foreign_key="week.id")
    day_id: Optional[int] = Field(default=None, foreign_key="dayplan.id")


class ResourceType(str, Enum):
    """Categorisation for reference material."""

    ARTICLE = "article"
    VIDEO = "video"
    BOOK = "book"
    COURSE = "course"
    TOOL = "tool"
    DOCS = "docs"
    SPEC = "spec"
    APPNOTE = "appnote"
    WHITEPAPER = "whitepaper"
    PAPER = "paper"
    BENCHMARK = "benchmark"
    CHECKLIST = "checklist"
    TEMPLATE = "template"
    GUIDE = "guide"
    PLATFORM = "platform"
    REPO = "repo"
    TALK = "talk"
    HANDS_ON = "hands-on"
    WORKSHEET = "worksheet"
    STANDARD = "standard"
    OTHER = "other"


class Resource(SQLModel, table=True):
    """Study material linked to a specific week."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: ResourceType = Field(default=ResourceType.OTHER)
    url: Optional[str] = None
    notes: Optional[str] = None

    week_id: int = Field(foreign_key="week.id")


class ProjectStatus(str, Enum):
    """Lifecycle state for roadmap projects."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ON_HOLD = "on_hold"


class Project(SQLModel, table=True):
    """Deliverables showcased in the portfolio tracker."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    status: ProjectStatus = Field(default=ProjectStatus.PLANNED)
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None

    phase_id: Optional[int] = Field(default=None, foreign_key="phase.id")


class CertificationStatus(str, Enum):
    """Progress stage for certifications."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class Certification(SQLModel, table=True):
    """Certification or course milestone to track."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    provider: Optional[str] = None
    due_date: Optional[date] = None
    completion_date: Optional[date] = None
    status: CertificationStatus = Field(default=CertificationStatus.PLANNED)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    credential_url: Optional[str] = None

    phase_id: Optional[int] = Field(default=None, foreign_key="phase.id")


class ApplicationStatus(str, Enum):
    """Hiring pipeline stage for job applications."""

    DRAFT = "draft"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"


class Application(SQLModel, table=True):
    """Job application log entry."""

    id: Optional[int] = Field(default=None, primary_key=True)
    company: str
    role: str
    source: Optional[str] = None
    status: ApplicationStatus = Field(default=ApplicationStatus.DRAFT)
    date_applied: Optional[date] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None


class Metric(SQLModel, table=True):
    """Quantitative signals such as hours logged or quiz scores."""

    id: Optional[int] = Field(default=None, primary_key=True)
    metric_type: str = Field(index=True)
    value: float
    unit: Optional[str] = None
    recorded_date: date = Field(default_factory=date.today)

    phase_id: Optional[int] = Field(default=None, foreign_key="phase.id")


class HardwareCategory(str, Enum):
    """Categories for hardware inventory items."""
    
    BOARD = "board"
    SENSOR = "sensor"
    MODULE = "module"
    RF_MODULE = "rf_module"
    DISPLAY = "display"
    ACTUATOR = "actuator"
    TOOL = "tool"
    CONNECTOR = "connector"
    POWER = "power"
    OTHER = "other"


class HardwareStatus(str, Enum):
    """Status of hardware inventory items."""
    
    AVAILABLE = "available"
    IN_USE = "in_use"
    ORDERED = "ordered"
    BROKEN = "broken"
    LENT = "lent"


class HardwareItem(SQLModel, table=True):
    """Hardware inventory item - boards, sensors, modules, tools."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: HardwareCategory = Field(default=HardwareCategory.OTHER)
    hardware_type: Optional[str] = None  # e.g., "gas", "proximity", "lora"
    mpn: Optional[str] = None  # Manufacturer Part Number
    mcu: Optional[str] = None  # For boards
    architecture: Optional[str] = None  # e.g., "ARM Cortex-M4"
    quantity: int = Field(default=1, ge=0)
    status: HardwareStatus = Field(default=HardwareStatus.AVAILABLE)
    specifications: Optional[str] = None  # Voltage/current ratings, etc.
    features: Optional[str] = None  # Comma-separated features
    interface: Optional[str] = None  # e.g., "I2C", "SPI", "UART"
    notes: Optional[str] = None  # Description/notes
    datasheet_url: Optional[str] = None  # Link to datasheet
    purchase_date: Optional[date] = None
    price_inr: Optional[float] = None
    
    # Link to project if in use
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")

