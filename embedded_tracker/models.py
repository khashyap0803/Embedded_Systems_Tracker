"""Database models representing the embedded systems roadmap domain."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SAEnum
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
    start_date: date
    end_date: date
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
    start_date: date
    end_date: date
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
    scheduled_date: date
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
