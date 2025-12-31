"""High-level data helpers used by both the CLI and the forthcoming GUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Iterable, List, Optional, Type

from sqlmodel import Session, select

from .db import session_scope
from .models import (
    Application,
    ApplicationStatus,
    Certification,
    CertificationStatus,
    DayPlan,
    HardwareCategory,
    HardwareItem,
    HardwareStatus,
    Metric,
    Phase,
    Project,
    ProjectStatus,
    Resource,
    ResourceType,
    Task,
    TaskStatus,
    Week,
)
from .utils import (
    ensure_utc as _ensure_utc,
    normalise_datetimes as _normalise_datetimes,
    seconds_between as _seconds_between,
    utcnow as _utcnow,
)
from .work_calendar import (
    get_calendar_config,
    add_work_days,
    next_work_day,
    list_work_days_in_range,
)

# Setup logging
try:
    from .logging_config import setup_logging
    logger = setup_logging(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


UNSET = object()


@dataclass(slots=True)
class PhaseRecord:
    id: int
    name: str
    description: Optional[str]
    start_date: date
    end_date: date
    status: TaskStatus
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    work_seconds: int
    break_seconds: int
    pause_seconds: int
    work_hours: float
    break_hours: float
    pause_hours: float


@dataclass(slots=True)
class WeekRecord:
    id: int
    number: int
    start_date: date
    end_date: date
    focus: Optional[str]
    phase_id: int
    phase_name: str
    status: TaskStatus
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    work_seconds: int
    break_seconds: int
    pause_seconds: int
    work_hours: float
    break_hours: float
    pause_hours: float


@dataclass(slots=True)
class DayRecord:
    id: int
    number: int
    scheduled_date: date
    focus: Optional[str]
    notes: Optional[str]
    status: TaskStatus
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    week_id: int
    week_number: int
    phase_id: int
    phase_name: str
    work_seconds: int
    break_seconds: int
    pause_seconds: int
    work_hours: float
    break_hours: float
    pause_hours: float
    hour_count: int


@dataclass(slots=True)
class TaskRecord:
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    ai_prompt: Optional[str]
    week_id: int
    week_number: int
    day_id: Optional[int]
    day_number: Optional[int]
    hour_number: Optional[int]
    phase_id: int
    phase_name: str
    status_updated_at: datetime
    first_started_at: Optional[datetime]
    completed_at: Optional[datetime]
    work_seconds: int
    break_seconds: int
    pause_seconds: int
    work_hours: float
    break_hours: float
    pause_hours: float
    is_running: bool
    is_on_break: bool
    is_paused: bool


@dataclass(slots=True)
class TimingSnapshot:
    work_seconds: int
    break_seconds: int
    pause_seconds: int
    running: bool
    on_break: bool
    paused: bool


@dataclass(slots=True)
class ResourceRecord:
    id: int
    title: str
    type: ResourceType
    url: Optional[str]
    notes: Optional[str]
    week_id: int
    week_number: int
    phase_id: int
    phase_name: str


@dataclass(slots=True)
class ProjectRecord:
    id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    repo_url: Optional[str]
    demo_url: Optional[str]
    start_date: Optional[date]
    due_date: Optional[date]
    phase_id: Optional[int]
    phase_name: str


@dataclass(slots=True)
class CertificationRecord:
    id: int
    name: str
    provider: Optional[str]
    due_date: Optional[date]
    completion_date: Optional[date]
    status: CertificationStatus
    progress: float
    credential_url: Optional[str]
    phase_id: Optional[int]
    phase_name: str


@dataclass(slots=True)
class ApplicationRecord:
    id: int
    company: str
    role: str
    source: Optional[str]
    status: ApplicationStatus
    date_applied: Optional[date]
    next_action: Optional[str]
    notes: Optional[str]


@dataclass(slots=True)
class MetricRecord:
    id: int
    metric_type: str
    value: float
    unit: Optional[str]
    recorded_date: date
    phase_id: Optional[int]
    phase_name: str


# -----------------------------------------------------------------------------
# Validation helpers
# -----------------------------------------------------------------------------

def _validate_date_range(start_date: date, end_date: date, entity_name: str = "Entity") -> None:
    """Validate that start_date is not after end_date."""
    if start_date > end_date:
        raise ValueError(f"{entity_name} start_date ({start_date}) cannot be after end_date ({end_date})")


# -----------------------------------------------------------------------------
# Phase helpers
# -----------------------------------------------------------------------------

def list_phases() -> List[PhaseRecord]:
    with session_scope() as session:
        rows = session.exec(select(Phase).order_by(Phase.start_date)).all()
        now = _utcnow()
        return [_phase_to_record(session, row, now) for row in rows]


def create_phase(*, name: str, description: Optional[str], start_date: date, end_date: date) -> PhaseRecord:
    _validate_date_range(start_date, end_date, "Phase")
    with session_scope() as session:
        phase = Phase(name=name, description=description, start_date=start_date, end_date=end_date)
        session.add(phase)
        session.flush()
        session.refresh(phase)
        return _phase_to_record(session, phase, _utcnow())



def update_phase(
    phase_id: int,
    *,
    name: object = UNSET,
    description: object = UNSET,
    start_date: object = UNSET,
    end_date: object = UNSET,
) -> PhaseRecord:
    with session_scope() as session:
        phase = session.get(Phase, phase_id)
        if phase is None:
            raise ValueError(f"Phase {phase_id} not found")
        if name is not UNSET:
            phase.name = name
        if description is not UNSET:
            phase.description = description
        
        # Track if start_date is changing
        start_date_changed = False
        new_start = None
        
        if start_date is not UNSET:
            old_start = phase.start_date
            new_start = start_date
            if old_start != new_start:
                start_date_changed = True
            phase.start_date = start_date
        if end_date is not UNSET:
            phase.end_date = end_date
        session.add(phase)
        session.flush()
        session.refresh(phase)
        result = _phase_to_record(session, phase, _utcnow())
    
    # If start_date changed, cascade to all subsequent dates (outside the transaction)
    if start_date_changed and new_start is not None:
        try:
            cascade_dates_from_phase_change(phase_id, new_start)
        except Exception as e:
            logger.warning(f"Could not cascade dates from phase update: {e}")
    
    return result


def delete_phase(phase_id: int) -> None:
    """Delete a phase and all its related data (weeks, days, tasks, resources, projects, certifications, metrics)."""
    with session_scope() as session:
        phase = session.get(Phase, phase_id)
        if phase is None:
            raise ValueError(f"Phase {phase_id} not found")
        
        # Delete all metrics associated with this phase
        metrics = session.exec(select(Metric).where(Metric.phase_id == phase_id)).all()
        for metric in metrics:
            session.delete(metric)
        
        # Delete all certifications associated with this phase
        certifications = session.exec(select(Certification).where(Certification.phase_id == phase_id)).all()
        for cert in certifications:
            session.delete(cert)
        
        # Delete all projects associated with this phase
        projects = session.exec(select(Project).where(Project.phase_id == phase_id)).all()
        for project in projects:
            session.delete(project)
        
        # Delete all weeks (which cascades to days, tasks, resources)
        weeks = session.exec(select(Week).where(Week.phase_id == phase_id)).all()
        for week in weeks:
            _delete_week_cascade(session, week)
        
        session.delete(phase)


# -----------------------------------------------------------------------------
# Week helpers
# -----------------------------------------------------------------------------

def list_weeks(*, phase_id: Optional[int] = None) -> List[WeekRecord]:
    with session_scope() as session:
        statement = select(Week, Phase).join(Phase, Week.phase_id == Phase.id)
        if phase_id is not None:
            statement = statement.where(Week.phase_id == phase_id)
        rows = session.exec(statement.order_by(Week.number)).all()
        now = _utcnow()
        return [_week_to_record(session, week, phase, now) for week, phase in rows]


def create_week(*, number: int, start_date: date, end_date: date, focus: Optional[str], phase_id: int) -> WeekRecord:
    _validate_date_range(start_date, end_date, "Week")
    with session_scope() as session:
        phase = session.get(Phase, phase_id)
        if phase is None:
            raise ValueError(f"Phase {phase_id} not found")
        week = Week(number=number, start_date=start_date, end_date=end_date, focus=focus, phase_id=phase_id)
        session.add(week)
        session.flush()
        session.refresh(week)
        return _week_to_record(session, week, phase, _utcnow())



def update_week(
    week_id: int,
    *,
    number: object = UNSET,
    start_date: object = UNSET,
    end_date: object = UNSET,
    focus: object = UNSET,
    phase_id: object = UNSET,
) -> WeekRecord:
    with session_scope() as session:
        week = session.get(Week, week_id)
        if week is None:
            raise ValueError(f"Week {week_id} not found")
        if number is not UNSET:
            week.number = number
        if start_date is not UNSET:
            week.start_date = start_date
        if end_date is not UNSET:
            week.end_date = end_date
        if focus is not UNSET:
            week.focus = focus
        if phase_id is not UNSET:
            phase = session.get(Phase, phase_id)
            if phase is None:
                raise ValueError(f"Phase {phase_id} not found")
            week.phase_id = phase_id
        session.add(week)
        session.flush()
        session.refresh(week)
        phase = session.get(Phase, week.phase_id)
        assert phase is not None
        return _week_to_record(session, week, phase, _utcnow())


def delete_week(week_id: int) -> None:
    """Delete a week and all its related data (days, tasks, resources)."""
    with session_scope() as session:
        week = session.get(Week, week_id)
        if week is None:
            raise ValueError(f"Week {week_id} not found")
        _delete_week_cascade(session, week)


def _delete_week_cascade(session: Session, week: Week) -> None:
    """Internal helper to delete week and all related data within an existing session."""
    # Delete all resources associated with this week
    resources = session.exec(select(Resource).where(Resource.week_id == week.id)).all()
    for resource in resources:
        session.delete(resource)
    
    # Delete all days (which cascades to tasks)
    days = session.exec(select(DayPlan).where(DayPlan.week_id == week.id)).all()
    for day in days:
        _delete_day_cascade(session, day)
    
    # Delete tasks that are directly linked to week (not through a day)
    tasks = session.exec(select(Task).where(Task.week_id == week.id)).all()
    for task in tasks:
        session.delete(task)
    
    session.delete(week)


# -----------------------------------------------------------------------------
# Day helpers
# -----------------------------------------------------------------------------


def list_days(*, phase_id: Optional[int] = None, week_id: Optional[int] = None) -> List[DayRecord]:
    with session_scope() as session:
        statement = (
            select(DayPlan, Week, Phase)
            .join(Week, DayPlan.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
        )
        if week_id is not None:
            statement = statement.where(DayPlan.week_id == week_id)
        if phase_id is not None:
            statement = statement.where(Week.phase_id == phase_id)
        rows = session.exec(statement.order_by(Week.number, DayPlan.number)).all()
        now = _utcnow()
        return [_day_to_record(session, day, week, phase, now) for day, week, phase in rows]


def create_day(
    *,
    number: int,
    scheduled_date: date,
    focus: Optional[str],
    notes: Optional[str],
    week_id: int,
) -> DayRecord:
    with session_scope() as session:
        week = session.get(Week, week_id)
        if week is None:
            raise ValueError(f"Week {week_id} not found")
        day = DayPlan(
            number=number,
            scheduled_date=scheduled_date,
            focus=focus,
            notes=notes,
            week_id=week_id,
        )
        session.add(day)
        session.flush()
        session.refresh(day)
        phase = session.get(Phase, week.phase_id)
        assert phase is not None
        return _day_to_record(session, day, week, phase, _utcnow())


def update_day(
    day_id: int,
    *,
    number: object = UNSET,
    scheduled_date: object = UNSET,
    focus: object = UNSET,
    notes: object = UNSET,
    week_id: object = UNSET,
) -> DayRecord:
    with session_scope() as session:
        day = session.get(DayPlan, day_id)
        if day is None:
            raise ValueError(f"Day {day_id} not found")
        if number is not UNSET:
            day.number = number
        if scheduled_date is not UNSET:
            day.scheduled_date = scheduled_date
        if focus is not UNSET:
            day.focus = focus
        if notes is not UNSET:
            day.notes = notes
        if week_id is not UNSET:
            week = session.get(Week, week_id)
            if week is None:
                raise ValueError(f"Week {week_id} not found")
            day.week_id = week_id
        session.add(day)
        session.flush()
        session.refresh(day)
        week = session.get(Week, day.week_id)
        assert week is not None
        phase = session.get(Phase, week.phase_id)
        assert phase is not None
        return _day_to_record(session, day, week, phase, _utcnow())


def override_day_status(day_id: int, new_status: TaskStatus) -> DayRecord:
    with session_scope() as session:
        day = session.get(DayPlan, day_id)
        if day is None:
            raise ValueError(f"Day {day_id} not found")
        has_tasks = (
            session.exec(select(Task.id).where(Task.day_id == day_id).limit(1)).first()
            is not None
        )
        if has_tasks:
            raise ValueError("This day has hour-level tasks. Update their statuses instead.")
        week = session.get(Week, day.week_id)
        if week is None:
            raise RuntimeError("Day missing associated week")
        phase = session.get(Phase, week.phase_id)
        if phase is None:
            raise RuntimeError("Week missing associated phase")
        now = _utcnow()
        _apply_manual_day_status(day, new_status, now)
        session.add(day)
        session.flush()
        _refresh_week_state(session, week, now)
        _refresh_phase_state(session, phase, now)
        session.flush()
        session.refresh(day)
        session.refresh(week)
        session.refresh(phase)
        return _day_to_record(session, day, week, phase, now)


def delete_day(day_id: int) -> None:
    """Delete a day and all its associated tasks."""
    with session_scope() as session:
        day = session.get(DayPlan, day_id)
        if day is None:
            raise ValueError(f"Day {day_id} not found")
        _delete_day_cascade(session, day)


def _delete_day_cascade(session: Session, day: DayPlan) -> None:
    """Internal helper to delete day and all related tasks within an existing session."""
    # Delete all tasks associated with this day
    tasks = session.exec(select(Task).where(Task.day_id == day.id)).all()
    for task in tasks:
        session.delete(task)
    
    session.delete(day)


# -----------------------------------------------------------------------------
# Task helpers
# -----------------------------------------------------------------------------

def list_tasks(
    *,
    phase_id: Optional[int] = None,
    week_id: Optional[int] = None,
    day_id: Optional[int] = None,
    only_open: bool = False,
    status: Optional[TaskStatus] = None,
) -> List[TaskRecord]:
    """List tasks with optional filters pushed to SQL level for performance."""
    open_states = {TaskStatus.PENDING, TaskStatus.WORKING, TaskStatus.BREAK, TaskStatus.PAUSED}
    with session_scope() as session:
        statement = (
            select(Task, Week, Phase, DayPlan)
            .join(Week, Task.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
            .join(DayPlan, Task.day_id == DayPlan.id, isouter=True)
        )
        if phase_id is not None:
            statement = statement.where(Week.phase_id == phase_id)
        if week_id is not None:
            statement = statement.where(Task.week_id == week_id)
        if day_id is not None:
            statement = statement.where(Task.day_id == day_id)
        if status is not None:
            statement = statement.where(Task.status == status)
        # Push only_open filter to SQL level (N+1 fix)
        if only_open:
            statement = statement.where(Task.status.in_(list(open_states)))
        now = _utcnow()
        rows: List[TaskRecord] = []
        ordered = session.exec(
            statement.order_by(Week.number, DayPlan.number.nulls_last(), Task.hour_number.nulls_last(), Task.title)
        ).all()
        for task, week, phase, day in ordered:
            rows.append(_task_to_record(session, task, week, phase, day, now))
        return rows


def create_task(
    *,
    title: str,
    description: Optional[str],
    status: TaskStatus = TaskStatus.PENDING,
    estimated_hours: Optional[float],
    actual_hours: Optional[float],
    ai_prompt: Optional[str],
    week_id: int,
    day_id: Optional[int],
    hour_number: Optional[int],
) -> TaskRecord:
    with session_scope() as session:
        week = session.get(Week, week_id)
        if week is None:
            raise ValueError(f"Week {week_id} not found")
        day = session.get(DayPlan, day_id) if day_id is not None else None
        if day_id is not None and day is None:
            raise ValueError(f"Day {day_id} not found")
        phase = session.get(Phase, week.phase_id)
        task = Task(
            title=title,
            description=description,
            status=_coerce_enum(status, TaskStatus),
            estimated_hours=estimated_hours,
            actual_hours=actual_hours,
            ai_prompt=ai_prompt,
            week_id=week_id,
            day_id=day_id,
            hour_number=hour_number,
        )
        session.add(task)
        session.flush()
        session.refresh(task)
        assert phase is not None
        return _task_to_record(session, task, week, phase, day, _utcnow())


def update_task(
    task_id: int,
    *,
    title: object = UNSET,
    description: object = UNSET,
    status: object = UNSET,
    estimated_hours: object = UNSET,
    actual_hours: object = UNSET,
    ai_prompt: object = UNSET,
    week_id: object = UNSET,
    day_id: object = UNSET,
    hour_number: object = UNSET,
) -> TaskRecord:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        if title is not UNSET:
            task.title = title
        if description is not UNSET:
            task.description = description
        if status is not UNSET:
            new_status = _coerce_enum(status, TaskStatus)
            if new_status != task.status:
                _transition_task_status(task, new_status, _utcnow())
            else:
                task.status_updated_at = _utcnow()
        if estimated_hours is not UNSET:
            task.estimated_hours = estimated_hours
        if actual_hours is not UNSET:
            task.actual_hours = actual_hours
        if ai_prompt is not UNSET:
            task.ai_prompt = ai_prompt
        if week_id is not UNSET:
            week = session.get(Week, week_id)
            if week is None:
                raise ValueError(f"Week {week_id} not found")
            task.week_id = week_id
        if day_id is not UNSET:
            if day_id is None:
                task.day_id = None
            else:
                day = session.get(DayPlan, day_id)
                if day is None:
                    raise ValueError(f"Day {day_id} not found")
                task.day_id = day_id
        if hour_number is not UNSET:
            task.hour_number = hour_number
        session.add(task)
        session.flush()
        session.refresh(task)
        week = session.get(Week, task.week_id)
        phase = session.get(Phase, week.phase_id) if week else None
        day = session.get(DayPlan, task.day_id) if task.day_id else None
        if week is None or phase is None:
            raise RuntimeError("Inconsistent task state: missing related week/phase")
        return _task_to_record(session, task, week, phase, day, _utcnow())


def delete_task(task_id: int) -> None:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        session.delete(task)


# -----------------------------------------------------------------------------
# Task status transitions
# -----------------------------------------------------------------------------


def update_task_status(task_id: int, new_status: TaskStatus) -> TaskRecord:
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")
        week = session.get(Week, task.week_id)
        if week is None:
            raise RuntimeError("Task missing associated week")
        phase = session.get(Phase, week.phase_id)
        if phase is None:
            raise RuntimeError("Task's week missing associated phase")
        day = session.get(DayPlan, task.day_id) if task.day_id else None
        now = _utcnow()
        _transition_task_status(task, new_status, now)
        session.add(task)
        session.flush()
        _update_container_status(session, day, week, phase, now)
        session.flush()
        session.refresh(task)
        if day is not None:
            session.refresh(day)
        session.refresh(week)
        session.refresh(phase)
        return _task_to_record(session, task, week, phase, day, now)


def reset_stale_tasks() -> int:
    """
    Find any tasks that are in WORKING state and reset them to PAUSED.
    This prevents the 'Zombie Timer' bug where tasks accumulate time
    across application restarts (crashes).
    
    Returns the number of tasks reset.
    """
    count = 0
    with session_scope() as session:
        tasks = session.exec(select(Task).where(Task.status == TaskStatus.WORKING)).all()
        for task in tasks:
            # We transition to PAUSED so the user knows it was running.
            # We do NOT add the time since last_work_started_at because we don't know
            # when the app crashed. Lost time is better than corrupt huge time.
            task.status = TaskStatus.PAUSED
            # Clear start time to prevent future calculations if anything checks it
            task.last_work_started_at = None
            session.add(task)
            count += 1
        
        if count > 0:
            logger.warning(f"Reset {count} stale WORKING tasks to PAUSED (Zombie Timer prevention)")
            
    return count


# -----------------------------------------------------------------------------
# Resource helpers
# -----------------------------------------------------------------------------

def list_resources(
    *,
    week_id: Optional[int] = None,
    phase_id: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
) -> List[ResourceRecord]:
    with session_scope() as session:
        statement = (
            select(Resource, Week, Phase)
            .join(Week, Resource.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
        )
        if week_id is not None:
            statement = statement.where(Resource.week_id == week_id)
        if phase_id is not None:
            statement = statement.where(Week.phase_id == phase_id)
        rows: List[ResourceRecord] = []
        for resource, week, phase in session.exec(statement.order_by(Week.number, Resource.title)).all():
            if resource_type is not None and resource.type != _coerce_enum(resource_type, ResourceType):
                continue
            rows.append(_resource_to_record(resource, week, phase))
        return rows


def create_resource(
    *,
    title: str,
    type: ResourceType,
    url: Optional[str],
    notes: Optional[str],
    week_id: int,
) -> ResourceRecord:
    with session_scope() as session:
        week = session.get(Week, week_id)
        if week is None:
            raise ValueError(f"Week {week_id} not found")
        phase = session.get(Phase, week.phase_id)
        resource = Resource(
            title=title,
            type=_coerce_enum(type, ResourceType),
            url=url,
            notes=notes,
            week_id=week_id,
        )
        session.add(resource)
        session.flush()
        session.refresh(resource)
        assert phase is not None
        return _resource_to_record(resource, week, phase)


def update_resource(
    resource_id: int,
    *,
    title: object = UNSET,
    type: object = UNSET,
    url: object = UNSET,
    notes: object = UNSET,
    week_id: object = UNSET,
) -> ResourceRecord:
    with session_scope() as session:
        resource = session.get(Resource, resource_id)
        if resource is None:
            raise ValueError(f"Resource {resource_id} not found")
        if title is not UNSET:
            resource.title = title
        if type is not UNSET:
            resource.type = _coerce_enum(type, ResourceType)
        if url is not UNSET:
            resource.url = url
        if notes is not UNSET:
            resource.notes = notes
        if week_id is not UNSET:
            week = session.get(Week, week_id)
            if week is None:
                raise ValueError(f"Week {week_id} not found")
            resource.week_id = week_id
        session.add(resource)
        session.flush()
        session.refresh(resource)
        week = session.get(Week, resource.week_id)
        phase = session.get(Phase, week.phase_id) if week else None
        if week is None or phase is None:
            raise RuntimeError("Inconsistent resource state: missing week/phase")
        return _resource_to_record(resource, week, phase)


def delete_resource(resource_id: int) -> None:
    with session_scope() as session:
        resource = session.get(Resource, resource_id)
        if resource is None:
            raise ValueError(f"Resource {resource_id} not found")
        session.delete(resource)


# -----------------------------------------------------------------------------
# Project helpers
# -----------------------------------------------------------------------------

def list_projects(*, phase_id: Optional[int] = None, status: Optional[ProjectStatus] = None) -> List[ProjectRecord]:
    with session_scope() as session:
        statement = select(Project, Phase).join(Phase, Project.phase_id == Phase.id, isouter=True)
        rows: List[ProjectRecord] = []
        for project, phase in session.exec(statement.order_by(Project.name)).all():
            if phase_id is not None and project.phase_id != phase_id:
                continue
            if status is not None and project.status != _coerce_enum(status, ProjectStatus):
                continue
            rows.append(_project_to_record(project, phase))
        return rows


def create_project(
    *,
    name: str,
    description: Optional[str],
    status: ProjectStatus,
    repo_url: Optional[str],
    demo_url: Optional[str],
    start_date: Optional[date],
    due_date: Optional[date],
    phase_id: Optional[int],
) -> ProjectRecord:
    with session_scope() as session:
        phase = session.get(Phase, phase_id) if phase_id is not None else None
        project = Project(
            name=name,
            description=description,
            status=_coerce_enum(status, ProjectStatus),
            repo_url=repo_url,
            demo_url=demo_url,
            start_date=start_date,
            due_date=due_date,
            phase_id=phase_id,
        )
        session.add(project)
        session.flush()
        session.refresh(project)
        return _project_to_record(project, phase)


def update_project(
    project_id: int,
    *,
    name: object = UNSET,
    description: object = UNSET,
    status: object = UNSET,
    repo_url: object = UNSET,
    demo_url: object = UNSET,
    start_date: object = UNSET,
    due_date: object = UNSET,
    phase_id: object = UNSET,
) -> ProjectRecord:
    with session_scope() as session:
        project = session.get(Project, project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")
        if name is not UNSET:
            project.name = name
        if description is not UNSET:
            project.description = description
        if status is not UNSET:
            project.status = _coerce_enum(status, ProjectStatus)
        if repo_url is not UNSET:
            project.repo_url = repo_url
        if demo_url is not UNSET:
            project.demo_url = demo_url
        if start_date is not UNSET:
            project.start_date = start_date
        if due_date is not UNSET:
            project.due_date = due_date
        if phase_id is not UNSET:
            if phase_id is not None:
                phase = session.get(Phase, phase_id)
                if phase is None:
                    raise ValueError(f"Phase {phase_id} not found")
            project.phase_id = phase_id
        session.add(project)
        session.flush()
        session.refresh(project)
        phase = session.get(Phase, project.phase_id) if project.phase_id else None
        return _project_to_record(project, phase)


def delete_project(project_id: int) -> None:
    with session_scope() as session:
        project = session.get(Project, project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")
        session.delete(project)


# -----------------------------------------------------------------------------
# Certification helpers
# -----------------------------------------------------------------------------

def list_certifications(*, status: Optional[CertificationStatus] = None) -> List[CertificationRecord]:
    with session_scope() as session:
        statement = select(Certification, Phase).join(Phase, Certification.phase_id == Phase.id, isouter=True)
        rows: List[CertificationRecord] = []
        for certification, phase in session.exec(statement.order_by(Certification.due_date, Certification.name)).all():
            if status is not None and certification.status != _coerce_enum(status, CertificationStatus):
                continue
            rows.append(_certification_to_record(certification, phase))
        return rows


def create_certification(
    *,
    name: str,
    provider: Optional[str],
    due_date: Optional[date],
    completion_date: Optional[date],
    status: CertificationStatus,
    progress: float,
    credential_url: Optional[str],
    phase_id: Optional[int],
) -> CertificationRecord:
    with session_scope() as session:
        phase = session.get(Phase, phase_id) if phase_id is not None else None
        certification = Certification(
            name=name,
            provider=provider,
            due_date=due_date,
            completion_date=completion_date,
            status=_coerce_enum(status, CertificationStatus),
            progress=progress,
            credential_url=credential_url,
            phase_id=phase_id,
        )
        session.add(certification)
        session.flush()
        session.refresh(certification)
        return _certification_to_record(certification, phase)


def update_certification(
    certification_id: int,
    *,
    name: object = UNSET,
    provider: object = UNSET,
    due_date: object = UNSET,
    completion_date: object = UNSET,
    status: object = UNSET,
    progress: object = UNSET,
    credential_url: object = UNSET,
    phase_id: object = UNSET,
) -> CertificationRecord:
    with session_scope() as session:
        certification = session.get(Certification, certification_id)
        if certification is None:
            raise ValueError(f"Certification {certification_id} not found")
        if name is not UNSET:
            certification.name = name
        if provider is not UNSET:
            certification.provider = provider
        if due_date is not UNSET:
            certification.due_date = due_date
        if completion_date is not UNSET:
            certification.completion_date = completion_date
        if status is not UNSET:
            certification.status = _coerce_enum(status, CertificationStatus)
        if progress is not UNSET:
            certification.progress = progress
        if credential_url is not UNSET:
            certification.credential_url = credential_url
        if phase_id is not UNSET:
            if phase_id is not None:
                phase = session.get(Phase, phase_id)
                if phase is None:
                    raise ValueError(f"Phase {phase_id} not found")
            certification.phase_id = phase_id
        session.add(certification)
        session.flush()
        session.refresh(certification)
        phase = session.get(Phase, certification.phase_id) if certification.phase_id else None
        return _certification_to_record(certification, phase)


def delete_certification(certification_id: int) -> None:
    with session_scope() as session:
        certification = session.get(Certification, certification_id)
        if certification is None:
            raise ValueError(f"Certification {certification_id} not found")
        session.delete(certification)


# -----------------------------------------------------------------------------
# Application helpers
# -----------------------------------------------------------------------------

def list_applications(*, status: Optional[ApplicationStatus] = None) -> List[ApplicationRecord]:
    with session_scope() as session:
        rows: List[ApplicationRecord] = []
        for application in session.exec(select(Application).order_by(Application.company)).all():
            if status is not None and application.status != _coerce_enum(status, ApplicationStatus):
                continue
            rows.append(_application_to_record(application))
        return rows


def create_application(
    *,
    company: str,
    role: str,
    source: Optional[str],
    status: ApplicationStatus,
    date_applied: Optional[date],
    next_action: Optional[str],
    notes: Optional[str],
) -> ApplicationRecord:
    with session_scope() as session:
        application = Application(
            company=company,
            role=role,
            source=source,
            status=_coerce_enum(status, ApplicationStatus),
            date_applied=date_applied,
            next_action=next_action,
            notes=notes,
        )
        session.add(application)
        session.flush()
        session.refresh(application)
        return _application_to_record(application)


def update_application(
    application_id: int,
    *,
    company: object = UNSET,
    role: object = UNSET,
    source: object = UNSET,
    status: object = UNSET,
    date_applied: object = UNSET,
    next_action: object = UNSET,
    notes: object = UNSET,
) -> ApplicationRecord:
    with session_scope() as session:
        application = session.get(Application, application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")
        if company is not UNSET:
            application.company = company
        if role is not UNSET:
            application.role = role
        if source is not UNSET:
            application.source = source
        if status is not UNSET:
            application.status = _coerce_enum(status, ApplicationStatus)
        if date_applied is not UNSET:
            application.date_applied = date_applied
        if next_action is not UNSET:
            application.next_action = next_action
        if notes is not UNSET:
            application.notes = notes
        session.add(application)
        session.flush()
        session.refresh(application)
        return _application_to_record(application)


def delete_application(application_id: int) -> None:
    with session_scope() as session:
        application = session.get(Application, application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")
        session.delete(application)


# -----------------------------------------------------------------------------
# Metric helpers
# -----------------------------------------------------------------------------

def list_metrics(*, metric_type: Optional[str] = None, phase_id: Optional[int] = None) -> List[MetricRecord]:
    with session_scope() as session:
        statement = select(Metric, Phase).join(Phase, Metric.phase_id == Phase.id, isouter=True)
        rows: List[MetricRecord] = []
        for metric, phase in session.exec(statement.order_by(Metric.recorded_date.desc())).all():
            if metric_type is not None and metric.metric_type.lower() != metric_type.lower():
                continue
            if phase_id is not None and metric.phase_id != phase_id:
                continue
            rows.append(_metric_to_record(metric, phase))
        return rows


def create_metric(
    *,
    metric_type: str,
    value: float,
    unit: Optional[str],
    recorded_date: date,
    phase_id: Optional[int],
) -> MetricRecord:
    with session_scope() as session:
        phase = session.get(Phase, phase_id) if phase_id is not None else None
        metric = Metric(
            metric_type=metric_type,
            value=value,
            unit=unit,
            recorded_date=recorded_date,
            phase_id=phase_id,
        )
        session.add(metric)
        session.flush()
        session.refresh(metric)
        return _metric_to_record(metric, phase)


def update_metric(
    metric_id: int,
    *,
    metric_type: object = UNSET,
    value: object = UNSET,
    unit: object = UNSET,
    recorded_date: object = UNSET,
    phase_id: object = UNSET,
) -> MetricRecord:
    with session_scope() as session:
        metric = session.get(Metric, metric_id)
        if metric is None:
            raise ValueError(f"Metric {metric_id} not found")
        if metric_type is not UNSET:
            metric.metric_type = metric_type
        if value is not UNSET:
            metric.value = value
        if unit is not UNSET:
            metric.unit = unit
        if recorded_date is not UNSET:
            metric.recorded_date = recorded_date
        if phase_id is not UNSET:
            if phase_id is not None:
                phase = session.get(Phase, phase_id)
                if phase is None:
                    raise ValueError(f"Phase {phase_id} not found")
            metric.phase_id = phase_id
        session.add(metric)
        session.flush()
        session.refresh(metric)
        phase = session.get(Phase, metric.phase_id) if metric.phase_id else None
        return _metric_to_record(metric, phase)


def delete_metric(metric_id: int) -> None:
    with session_scope() as session:
        metric = session.get(Metric, metric_id)
        if metric is None:
            raise ValueError(f"Metric {metric_id} not found")
        session.delete(metric)


# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------

def _coerce_enum(value, enum_cls: Type[Enum]):  # type: ignore[type-arg]
    if value is None or isinstance(value, enum_cls):
        return value
    return enum_cls(value)





def _task_timing_snapshot(task: Task, now: datetime) -> TimingSnapshot:
    work_seconds = task.total_work_seconds
    break_seconds = task.total_break_seconds
    pause_seconds = task.total_pause_seconds
    running = False
    on_break = False
    paused = False
    if task.status == TaskStatus.WORKING and task.last_work_started_at:
        work_seconds += _seconds_between(task.last_work_started_at, now)
        running = True
    if task.status == TaskStatus.BREAK and task.last_break_started_at:
        break_seconds += _seconds_between(task.last_break_started_at, now)
        on_break = True
    if task.status == TaskStatus.PAUSED and task.last_pause_started_at:
        pause_seconds += _seconds_between(task.last_pause_started_at, now)
        paused = True
    return TimingSnapshot(
        work_seconds=int(work_seconds),
        break_seconds=int(break_seconds),
        pause_seconds=int(pause_seconds),
        running=running,
        on_break=on_break,
        paused=paused,
    )


def _aggregate_task_collection(tasks: Iterable[Task], now: datetime) -> tuple[int, int, int]:
    work = break_seconds = pause = 0
    for task in tasks:
        snapshot = _task_timing_snapshot(task, now)
        work += snapshot.work_seconds
        break_seconds += snapshot.break_seconds
        pause += snapshot.pause_seconds
    return work, break_seconds, pause


def _aggregate_day_totals(session: Session, day_id: int, now: datetime) -> tuple[int, int, int, int]:
    tasks = session.exec(select(Task).where(Task.day_id == day_id)).all()
    work, break_seconds, pause = _aggregate_task_collection(tasks, now)
    return work, break_seconds, pause, len(tasks)


def _aggregate_week_totals(session: Session, week_id: int, now: datetime) -> tuple[int, int, int]:
    tasks = session.exec(select(Task).where(Task.week_id == week_id)).all()
    return _aggregate_task_collection(tasks, now)


def _aggregate_phase_totals(session: Session, phase_id: int, now: datetime) -> tuple[int, int, int]:
    tasks = session.exec(
        select(Task)
        .join(Week, Task.week_id == Week.id)
        .where(Week.phase_id == phase_id)
    ).all()
    return _aggregate_task_collection(tasks, now)


def _phase_to_record(session: Session, phase: Phase, now: datetime) -> PhaseRecord:
    if phase.id is None:
        work = break_seconds = pause = 0
    else:
        work, break_seconds, pause = _aggregate_phase_totals(session, phase.id, now)
    return PhaseRecord(
        id=phase.id or 0,
        name=phase.name,
        description=phase.description,
        start_date=phase.start_date,
        end_date=phase.end_date,
        status=phase.status,
        actual_start=phase.actual_start,
        actual_end=phase.actual_end,
        work_seconds=work,
        break_seconds=break_seconds,
        pause_seconds=pause,
        work_hours=work / 3600.0,
        break_hours=break_seconds / 3600.0,
        pause_hours=pause / 3600.0,
    )


def _week_to_record(session: Session, week: Week, phase: Phase, now: datetime) -> WeekRecord:
    if week.id is None:
        work = break_seconds = pause = 0
    else:
        work, break_seconds, pause = _aggregate_week_totals(session, week.id, now)
    return WeekRecord(
        id=week.id or 0,
        number=week.number,
        start_date=week.start_date,
        end_date=week.end_date,
        focus=week.focus,
        phase_id=phase.id or week.phase_id,
        phase_name=phase.name,
        status=week.status,
        actual_start=week.actual_start,
        actual_end=week.actual_end,
        work_seconds=work,
        break_seconds=break_seconds,
        pause_seconds=pause,
        work_hours=work / 3600.0,
        break_hours=break_seconds / 3600.0,
        pause_hours=pause / 3600.0,
    )


def _day_to_record(session: Session, day: DayPlan, week: Week, phase: Phase, now: datetime) -> DayRecord:
    work, break_seconds, pause, hour_count = _aggregate_day_totals(session, day.id or 0, now)
    return DayRecord(
        id=day.id or 0,
        number=day.number,
        scheduled_date=day.scheduled_date,
        focus=day.focus,
        notes=day.notes,
        status=day.status,
        actual_start=day.actual_start,
        actual_end=day.actual_end,
        week_id=week.id or day.week_id,
        week_number=week.number,
        phase_id=phase.id or week.phase_id,
        phase_name=phase.name,
        work_seconds=work,
        break_seconds=break_seconds,
        pause_seconds=pause,
        work_hours=work / 3600.0,
        break_hours=break_seconds / 3600.0,
        pause_hours=pause / 3600.0,
        hour_count=hour_count,
    )


def _task_to_record(
    session: Session,
    task: Task,
    week: Week,
    phase: Phase,
    day: Optional[DayPlan],
    now: datetime,
) -> TaskRecord:
    snapshot = _task_timing_snapshot(task, now)
    return TaskRecord(
        id=task.id or 0,
        title=task.title,
        description=task.description,
        status=task.status,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        ai_prompt=task.ai_prompt,
        week_id=week.id or task.week_id,
        week_number=week.number,
        day_id=day.id if day else task.day_id,
        day_number=day.number if day else None,
        hour_number=task.hour_number,
        phase_id=phase.id or week.phase_id,
        phase_name=phase.name,
        status_updated_at=_ensure_utc(task.status_updated_at) or _utcnow(),
        first_started_at=_ensure_utc(task.first_started_at),
        completed_at=_ensure_utc(task.completed_at),
        work_seconds=snapshot.work_seconds,
        break_seconds=snapshot.break_seconds,
        pause_seconds=snapshot.pause_seconds,
        work_hours=snapshot.work_seconds / 3600.0,
        break_hours=snapshot.break_seconds / 3600.0,
        pause_hours=snapshot.pause_seconds / 3600.0,
        is_running=snapshot.running,
        is_on_break=snapshot.on_break,
        is_paused=snapshot.paused,
    )


def _apply_manual_day_status(day: DayPlan, new_status: TaskStatus, now: datetime) -> None:
    timestamp = _ensure_utc(now) or _utcnow()
    if new_status == TaskStatus.PENDING:
        day.status = TaskStatus.PENDING
        day.actual_start = None
        day.actual_end = None
        return
    day.status = new_status
    if day.actual_start is None:
        day.actual_start = timestamp
    if new_status == TaskStatus.COMPLETED:
        day.actual_end = timestamp
    else:
        day.actual_end = None


def _transition_task_status(task: Task, new_status: TaskStatus, now: datetime) -> None:
    if task.status == new_status:
        if new_status == TaskStatus.WORKING and task.last_work_started_at is None:
            task.last_work_started_at = now
            if task.first_started_at is None:
                task.first_started_at = now
        task.status_updated_at = now
        return
    _finalise_active_segment(task, now)
    if new_status == TaskStatus.PENDING:
        task.status = TaskStatus.PENDING
        task.status_updated_at = now
        task.first_started_at = None
        task.completed_at = None
        task.last_work_started_at = None
        task.last_break_started_at = None
        task.last_pause_started_at = None
        task.total_work_seconds = 0
        task.total_break_seconds = 0
        task.total_pause_seconds = 0
        return
    if new_status == TaskStatus.WORKING:
        if task.first_started_at is None:
            task.first_started_at = now
            # When very first task is started, calculate plan dates for entire roadmap
            try:
                calculate_plan_dates_from_start(now.date())
            except Exception as e:
                logger.warning(f"Could not calculate plan dates: {e}")
        task.last_work_started_at = now
        task.last_break_started_at = None
        task.last_pause_started_at = None
        task.completed_at = None
    elif new_status == TaskStatus.BREAK:
        task.last_break_started_at = now
        task.last_work_started_at = None
        task.last_pause_started_at = None
    elif new_status == TaskStatus.PAUSED:
        task.last_pause_started_at = now
        task.last_work_started_at = None
        task.last_break_started_at = None
    elif new_status == TaskStatus.COMPLETED:
        task.completed_at = now
        task.last_work_started_at = None
        task.last_break_started_at = None
        task.last_pause_started_at = None
    task.status = new_status
    task.status_updated_at = now


def _finalise_active_segment(task: Task, now: datetime) -> None:
    if task.status == TaskStatus.WORKING and task.last_work_started_at:
        task.total_work_seconds += _seconds_between(task.last_work_started_at, now)
        task.last_work_started_at = None
    elif task.status == TaskStatus.BREAK and task.last_break_started_at:
        task.total_break_seconds += _seconds_between(task.last_break_started_at, now)
        task.last_break_started_at = None
    elif task.status == TaskStatus.PAUSED and task.last_pause_started_at:
        task.total_pause_seconds += _seconds_between(task.last_pause_started_at, now)
        task.last_pause_started_at = None


def _update_container_status(
    session: Session,
    day: Optional[DayPlan],
    week: Week,
    phase: Phase,
    now: datetime,
) -> None:
    if day is not None:
        _refresh_day_state(session, day, now)
    _refresh_week_state(session, week, now)
    _refresh_phase_state(session, phase, now)


def _refresh_day_state(session: Session, day: DayPlan, now: datetime) -> None:
    tasks = session.exec(select(Task).where(Task.day_id == day.id)).all()
    if not tasks:
        session.add(day)
        return
    child_statuses = [task.status for task in tasks]
    new_status = _derive_container_status(child_statuses)
    day.status = new_status
    if new_status == TaskStatus.PENDING:
        day.actual_start = None
        day.actual_end = None
    else:
        start_candidates = _normalise_datetimes(task.first_started_at for task in tasks)
        if start_candidates:
            earliest = min(start_candidates)
            current_start = _ensure_utc(day.actual_start)
            day.actual_start = earliest if current_start is None else min(current_start, earliest)
        if new_status == TaskStatus.COMPLETED:
            end_candidates = _normalise_datetimes(task.completed_at for task in tasks)
            if end_candidates:
                day.actual_end = max(end_candidates)
        else:
            day.actual_end = None
    session.add(day)


def _refresh_week_state(session: Session, week: Week, now: datetime) -> None:
    days = session.exec(select(DayPlan).where(DayPlan.week_id == week.id)).all()
    if days:
        child_statuses = [day.status for day in days]
        new_status = _derive_container_status(child_statuses)
        week.status = new_status
        if new_status == TaskStatus.PENDING:
            week.actual_start = None
            week.actual_end = None
        else:
            start_candidates = _normalise_datetimes(day.actual_start for day in days)
            if not start_candidates:
                tasks = session.exec(select(Task).where(Task.week_id == week.id)).all()
                start_candidates = _normalise_datetimes(task.first_started_at for task in tasks)
            if start_candidates:
                earliest = min(start_candidates)
                current_start = _ensure_utc(week.actual_start)
                week.actual_start = earliest if current_start is None else min(current_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = _normalise_datetimes(day.actual_end for day in days)
                if end_candidates:
                    week.actual_end = max(end_candidates)
            else:
                week.actual_end = None
    else:
        tasks = session.exec(select(Task).where(Task.week_id == week.id)).all()
        child_statuses = [task.status for task in tasks]
        new_status = _derive_container_status(child_statuses)
        week.status = new_status
        if new_status == TaskStatus.PENDING:
            week.actual_start = None
            week.actual_end = None
        else:
            start_candidates = _normalise_datetimes(task.first_started_at for task in tasks)
            if start_candidates:
                earliest = min(start_candidates)
                current_start = _ensure_utc(week.actual_start)
                week.actual_start = earliest if current_start is None else min(current_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = _normalise_datetimes(task.completed_at for task in tasks)
                if end_candidates:
                    week.actual_end = max(end_candidates)
            else:
                week.actual_end = None
    session.add(week)


def _refresh_phase_state(session: Session, phase: Phase, now: datetime) -> None:
    weeks = session.exec(select(Week).where(Week.phase_id == phase.id)).all()
    if weeks:
        child_statuses = [week.status for week in weeks]
        new_status = _derive_container_status(child_statuses)
        phase.status = new_status
        if new_status == TaskStatus.PENDING:
            phase.actual_start = None
            phase.actual_end = None
        else:
            start_candidates = _normalise_datetimes(week.actual_start for week in weeks)
            if not start_candidates:
                tasks = session.exec(
                    select(Task)
                    .join(Week, Task.week_id == Week.id)
                    .where(Week.phase_id == phase.id)
                ).all()
                start_candidates = _normalise_datetimes(task.first_started_at for task in tasks)
            if start_candidates:
                earliest = min(start_candidates)
                current_start = _ensure_utc(phase.actual_start)
                phase.actual_start = earliest if current_start is None else min(current_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = _normalise_datetimes(week.actual_end for week in weeks)
                if end_candidates:
                    phase.actual_end = max(end_candidates)
            else:
                phase.actual_end = None
    else:
        tasks = session.exec(
            select(Task)
            .join(Week, Task.week_id == Week.id)
            .where(Week.phase_id == phase.id)
        ).all()
        child_statuses = [task.status for task in tasks]
        new_status = _derive_container_status(child_statuses)
        phase.status = new_status
        if new_status == TaskStatus.PENDING:
            phase.actual_start = None
            phase.actual_end = None
        else:
            start_candidates = _normalise_datetimes(task.first_started_at for task in tasks)
            if start_candidates:
                earliest = min(start_candidates)
                current_start = _ensure_utc(phase.actual_start)
                phase.actual_start = earliest if current_start is None else min(current_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = _normalise_datetimes(task.completed_at for task in tasks)
                if end_candidates:
                    phase.actual_end = max(end_candidates)
            else:
                phase.actual_end = None
    session.add(phase)


def _derive_container_status(child_statuses: Iterable[TaskStatus]) -> TaskStatus:
    statuses = set(child_statuses)
    if not statuses or statuses == {TaskStatus.PENDING}:
        return TaskStatus.PENDING
    if TaskStatus.WORKING in statuses:
        return TaskStatus.WORKING
    if TaskStatus.BREAK in statuses or TaskStatus.PAUSED in statuses:
        return TaskStatus.PAUSED
    if statuses == {TaskStatus.COMPLETED}:
        return TaskStatus.COMPLETED
    return TaskStatus.PAUSED


def calculate_plan_dates_from_start(start_date: date) -> bool:
    """
    Calculate plan dates for all phases and weeks based on a start date.
    Called when the first task is started to set up the schedule dynamically.
    
    Uses the work calendar to respect weekends and holidays. Each week contains
    a configurable number of work days (default: 6 days per week).
    
    Returns True if plan dates were calculated, False if already set.
    """
    from datetime import timedelta
    config = get_calendar_config()
    
    with session_scope() as session:
        # Check if plan dates are already set (don't recalculate)
        phases = session.exec(select(Phase).order_by(Phase.id)).all()
        if phases and phases[0].start_date is not None:
            return False  # Already calculated
        
        weeks = session.exec(select(Week).order_by(Week.number)).all()
        
        # Calculate week dates using work calendar
        current_date = next_work_day(start_date, config)
        for week in weeks:
            week.start_date = current_date
            # Each week has config.days_per_week work days
            week.end_date = add_work_days(current_date, config.days_per_week - 1, config)
            # Next week starts on the next work day after this week ends
            current_date = next_work_day(week.end_date + timedelta(days=1), config)
            session.add(week)
        
        # Calculate phase dates from their weeks
        for phase in phases:
            phase_weeks = [w for w in weeks if w.phase_id == phase.id]
            if phase_weeks:
                phase.start_date = phase_weeks[0].start_date
                phase.end_date = phase_weeks[-1].end_date
                session.add(phase)
        
        logger.info(f"Calculated plan dates (work calendar) starting from {start_date} for {len(weeks)} weeks")
        return True


def recalculate_all_plan_dates(new_start_date: date) -> None:
    """
    Force recalculate all plan dates from a new start date.
    Updates phases, weeks, and days. Useful if user wants to reset their schedule.
    
    Uses work calendar to respect weekends and holidays.
    """
    from datetime import timedelta
    config = get_calendar_config()
    
    with session_scope() as session:
        phases = session.exec(select(Phase).order_by(Phase.id)).all()
        weeks = session.exec(select(Week).order_by(Week.number)).all()
        
        # Calculate week dates using work calendar
        current_date = next_work_day(new_start_date, config)
        for week in weeks:
            week.start_date = current_date
            week.end_date = add_work_days(current_date, config.days_per_week - 1, config)
            
            # Also update days within this week - only on work days
            days = session.exec(select(DayPlan).where(DayPlan.week_id == week.id).order_by(DayPlan.number)).all()
            work_days_in_week = list_work_days_in_range(week.start_date, week.end_date, config)
            for i, day in enumerate(days):
                if i < len(work_days_in_week):
                    day.scheduled_date = work_days_in_week[i]
                else:
                    # Extend into next work days if more days than expected
                    day.scheduled_date = add_work_days(week.start_date, i, config)
                session.add(day)
            
            current_date = next_work_day(week.end_date + timedelta(days=1), config)
            session.add(week)
        
        # Calculate phase dates from their weeks
        for phase in phases:
            phase_weeks = [w for w in weeks if w.phase_id == phase.id]
            if phase_weeks:
                phase.start_date = phase_weeks[0].start_date
                phase.end_date = phase_weeks[-1].end_date
                session.add(phase)
        
        logger.info(f"Recalculated all plan dates (work calendar) from {new_start_date}")


def cascade_dates_from_phase_change(phase_id: int, new_start_date: date) -> None:
    """
    When a phase's start date is changed, recalculate all dates from that point.
    This allows user to adjust the schedule by changing Phase 1's start date.
    
    Uses work calendar to respect weekends and holidays.
    """
    from datetime import timedelta
    config = get_calendar_config()
    
    with session_scope() as session:
        # Get all phases ordered
        phases = session.exec(select(Phase).order_by(Phase.id)).all()
        
        # Find the changed phase
        target_phase = next((p for p in phases if p.id == phase_id), None)
        if not target_phase:
            return
        
        # Get all weeks in order
        weeks = session.exec(select(Week).order_by(Week.number)).all()
        
        # Find weeks belonging to this phase and later
        target_phase_weeks = [w for w in weeks if w.phase_id == phase_id]
        if not target_phase_weeks:
            return
        
        first_week_num = target_phase_weeks[0].number
        
        # Calculate from the new start date using work calendar
        current_date = next_work_day(new_start_date, config)
        for week in weeks:
            if week.number >= first_week_num:
                week.start_date = current_date
                week.end_date = add_work_days(current_date, config.days_per_week - 1, config)
                
                # Update days - only on work days
                days = session.exec(select(DayPlan).where(DayPlan.week_id == week.id).order_by(DayPlan.number)).all()
                work_days_in_week = list_work_days_in_range(week.start_date, week.end_date, config)
                for i, day in enumerate(days):
                    if i < len(work_days_in_week):
                        day.scheduled_date = work_days_in_week[i]
                    else:
                        day.scheduled_date = add_work_days(week.start_date, i, config)
                    session.add(day)
                
                current_date = next_work_day(week.end_date + timedelta(days=1), config)
                session.add(week)
        
        # Update phase dates from their weeks
        for phase in phases:
            phase_weeks = [w for w in weeks if w.phase_id == phase.id]
            if phase_weeks:
                phase.start_date = phase_weeks[0].start_date
                phase.end_date = phase_weeks[-1].end_date
                session.add(phase)
        
        logger.info(f"Cascaded dates (work calendar) from phase {phase_id} starting {new_start_date}")


def _resource_to_record(resource: Resource, week: Week, phase: Phase) -> ResourceRecord:
    return ResourceRecord(
        id=resource.id or 0,
        title=resource.title,
        type=resource.type,
        url=resource.url,
        notes=resource.notes,
        week_id=week.id or resource.week_id,
        week_number=week.number,
        phase_id=phase.id or week.phase_id,
        phase_name=phase.name,
    )


def _project_to_record(project: Project, phase: Optional[Phase]) -> ProjectRecord:
    return ProjectRecord(
        id=project.id or 0,
        name=project.name,
        description=project.description,
        status=project.status,
        repo_url=project.repo_url,
        demo_url=project.demo_url,
        start_date=project.start_date,
        due_date=project.due_date,
        phase_id=project.phase_id,
        phase_name=phase.name if phase else "Unassigned",
    )


def _certification_to_record(certification: Certification, phase: Optional[Phase]) -> CertificationRecord:
    return CertificationRecord(
        id=certification.id or 0,
        name=certification.name,
        provider=certification.provider,
        due_date=certification.due_date,
        completion_date=certification.completion_date,
        status=certification.status,
        progress=certification.progress,
        credential_url=certification.credential_url,
        phase_id=certification.phase_id,
        phase_name=phase.name if phase else "Unassigned",
    )


def _application_to_record(application: Application) -> ApplicationRecord:
    return ApplicationRecord(
        id=application.id or 0,
        company=application.company,
        role=application.role,
        source=application.source,
        status=application.status,
        date_applied=application.date_applied,
        next_action=application.next_action,
        notes=application.notes,
    )


def _metric_to_record(metric: Metric, phase: Optional[Phase]) -> MetricRecord:
    return MetricRecord(
        id=metric.id or 0,
        metric_type=metric.metric_type,
        value=metric.value,
        unit=metric.unit,
        recorded_date=metric.recorded_date,
        phase_id=metric.phase_id,
        phase_name=phase.name if phase else "Unassigned",
    )


# -----------------------------------------------------------------------------
# Hardware Inventory helpers
# -----------------------------------------------------------------------------

@dataclass(slots=True)
class HardwareRecord:
    """Record representing a hardware inventory item."""
    id: int
    name: str
    category: HardwareCategory
    hardware_type: Optional[str]
    mcu: Optional[str]
    architecture: Optional[str]
    quantity: int
    status: HardwareStatus
    specifications: Optional[str]
    features: Optional[str]
    interface: Optional[str]
    notes: Optional[str]
    purchase_date: Optional[date]
    price_inr: Optional[float]
    project_id: Optional[int]
    project_name: Optional[str]


def _hardware_to_record(item: HardwareItem, project: Optional[Project] = None) -> HardwareRecord:
    """Convert HardwareItem model to HardwareRecord dataclass."""
    return HardwareRecord(
        id=item.id or 0,
        name=item.name,
        category=item.category,
        hardware_type=item.hardware_type,
        mcu=item.mcu,
        architecture=item.architecture,
        quantity=item.quantity,
        status=item.status,
        specifications=item.specifications,
        features=item.features,
        interface=item.interface,
        notes=item.notes,
        purchase_date=item.purchase_date,
        price_inr=item.price_inr,
        project_id=item.project_id,
        project_name=project.name if project else None,
    )


def list_hardware(
    category: Optional[HardwareCategory] = None,
    status: Optional[HardwareStatus] = None,
) -> List[HardwareRecord]:
    """List hardware items with optional filtering."""
    with session_scope() as session:
        statement = select(HardwareItem, Project).join(
            Project, HardwareItem.project_id == Project.id, isouter=True
        )
        if category is not None:
            statement = statement.where(HardwareItem.category == category)
        if status is not None:
            statement = statement.where(HardwareItem.status == status)
        # Order by ID for proper ascending order (1, 2, 3, ...)
        statement = statement.order_by(HardwareItem.id)
        rows = session.exec(statement).all()
        return [_hardware_to_record(item, project) for item, project in rows]


def create_hardware(
    *,
    name: str,
    category: HardwareCategory,
    hardware_type: Optional[str] = None,
    mcu: Optional[str] = None,
    architecture: Optional[str] = None,
    quantity: int = 1,
    status: HardwareStatus = HardwareStatus.AVAILABLE,
    specifications: Optional[str] = None,
    features: Optional[str] = None,
    interface: Optional[str] = None,
    notes: Optional[str] = None,
    price_inr: Optional[float] = None,
    project_id: Optional[int] = None,
) -> HardwareRecord:
    """Create a new hardware inventory item."""
    with session_scope() as session:
        item = HardwareItem(
            name=name,
            category=category,
            hardware_type=hardware_type,
            mcu=mcu,
            architecture=architecture,
            quantity=quantity,
            status=status,
            specifications=specifications,
            features=features,
            interface=interface,
            notes=notes,
            price_inr=price_inr,
            project_id=project_id,
        )
        session.add(item)
        session.flush()
        session.refresh(item)
        project = session.get(Project, item.project_id) if item.project_id else None
        return _hardware_to_record(item, project)


def update_hardware(
    hardware_id: int,
    *,
    name: object = UNSET,
    category: object = UNSET,
    hardware_type: object = UNSET,
    quantity: object = UNSET,
    status: object = UNSET,
    notes: object = UNSET,
    project_id: object = UNSET,
) -> HardwareRecord:
    """Update a hardware item."""
    with session_scope() as session:
        item = session.get(HardwareItem, hardware_id)
        if item is None:
            raise ValueError(f"Hardware item {hardware_id} not found")
        if name is not UNSET:
            item.name = name
        if category is not UNSET:
            item.category = category
        if hardware_type is not UNSET:
            item.hardware_type = hardware_type
        if quantity is not UNSET:
            item.quantity = quantity
        if status is not UNSET:
            item.status = status
        if notes is not UNSET:
            item.notes = notes
        if project_id is not UNSET:
            item.project_id = project_id
        session.add(item)
        session.flush()
        session.refresh(item)
        project = session.get(Project, item.project_id) if item.project_id else None
        return _hardware_to_record(item, project)


def delete_hardware(hardware_id: int) -> None:
    """Delete a hardware item."""
    with session_scope() as session:
        item = session.get(HardwareItem, hardware_id)
        if item is None:
            raise ValueError(f"Hardware item {hardware_id} not found")
        session.delete(item)


def assign_hardware_to_project(hardware_id: int, project_id: Optional[int]) -> HardwareRecord:
    """Assign or unassign hardware to a project."""
    status = HardwareStatus.IN_USE if project_id else HardwareStatus.AVAILABLE
    return update_hardware(hardware_id, project_id=project_id, status=status)


# -----------------------------------------------------------------------------
# JSON Data Loaders
# -----------------------------------------------------------------------------

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data"


def get_system_specs() -> dict:
    """Load and return system specifications from JSON."""
    specs_path = _DATA_DIR / "system_specs.json"
    if not specs_path.exists():
        return {}
    try:
        with open(specs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load system specs: {e}")
        return {}


def get_hardware_bom() -> dict:
    """Load and return hardware BOM from JSON."""
    bom_path = _DATA_DIR / "hardware_bom.json"
    if not bom_path.exists():
        return {}
    try:
        with open(bom_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load hardware BOM: {e}")
        return {}


def get_hardware_inventory_json() -> dict:
    """Load and return hardware inventory from JSON."""
    inv_path = _DATA_DIR / "hardware_inventory.json"
    if not inv_path.exists():
        return {}
    try:
        with open(inv_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load hardware inventory: {e}")
        return {}


def seed_hardware_from_json() -> int:
    """Seed hardware inventory from JSON file. Returns count of items added."""
    inventory = get_hardware_inventory_json()
    if not inventory:
        return 0
    
    count = 0
    category_map = {
        "boards": HardwareCategory.BOARD,
        "sensors": HardwareCategory.SENSOR,
        "modules": HardwareCategory.MODULE,
        "rf_modules": HardwareCategory.RF_MODULE,
        "displays": HardwareCategory.DISPLAY,
        "actuators": HardwareCategory.ACTUATOR,
        "tools": HardwareCategory.TOOL,
    }
    
    with session_scope() as session:
        for category_key, category_enum in category_map.items():
            items = inventory.get(category_key, [])
            for item_data in items:
                # Check if item already exists
                existing = session.exec(
                    select(HardwareItem).where(HardwareItem.name == item_data.get("name"))
                ).first()
                if existing:
                    continue
                
                hw_item = HardwareItem(
                    name=item_data.get("name", "Unknown"),
                    category=category_enum,
                    hardware_type=item_data.get("type"),
                    mcu=item_data.get("mcu"),
                    architecture=item_data.get("architecture"),
                    quantity=item_data.get("quantity", 1),
                    status=HardwareStatus.AVAILABLE,
                    interface=item_data.get("interface"),
                    notes=item_data.get("notes"),
                    features=",".join(item_data.get("features", [])) if item_data.get("features") else None,
                )
                session.add(hw_item)
                count += 1
    
    logger.info(f"Seeded {count} hardware items from inventory JSON")
    return count


def compare_inventory_vs_bom() -> dict:
    """Compare current inventory against BOM to find missing items."""
    bom = get_hardware_bom()
    if not bom:
        return {"missing": [], "owned": [], "extra": []}
    
    # Get all items from BOM
    bom_items = {}
    for category_data in bom.get("categories", {}).values():
        for item in category_data.get("items", []):
            bom_items[item["name"].lower()] = item
    
    # Get inventory from database
    inventory = list_hardware()
    inventory_names = {item.name.lower() for item in inventory}
    
    # Find missing (in BOM but not in inventory)
    missing = []
    for name, item in bom_items.items():
        if name not in inventory_names:
            missing.append({
                "name": item["name"],
                "priority": item.get("priority", "optional"),
                "price_inr": item.get("price_inr", 0),
                "phase_needed": item.get("phase_needed"),
                "week_needed": item.get("week_needed"),
            })
    
    # Sort missing by priority and phase
    priority_order = {"essential": 0, "recommended": 1, "optional": 2}
    missing.sort(key=lambda x: (priority_order.get(x["priority"], 3), x.get("phase_needed", 99)))
    
    return {
        "missing": missing,
        "owned_count": len(inventory),
        "bom_total": len(bom_items),
        "coverage_percent": round(100 * (len(bom_items) - len(missing)) / max(len(bom_items), 1), 1),
    }


def get_pre_week1_checklist() -> dict:
    """Load and return pre-Week-1 environment setup checklist."""
    checklist_path = _DATA_DIR / "pre_week1_checklist.json"
    if not checklist_path.exists():
        return {}
    try:
        with open(checklist_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load pre-Week-1 checklist: {e}")
        return {}


def get_roadmap_audit_patches() -> dict:
    """Load and return roadmap audit patches (buffer weeks, new topics)."""
    patches_path = _DATA_DIR / "roadmap_audit_patches.json"
    if not patches_path.exists():
        return {}
    try:
        with open(patches_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load roadmap audit patches: {e}")
        return {}


def get_all_data_files() -> dict:
    """Return a summary of all data files available."""
    return {
        "system_specs": bool(get_system_specs()),
        "hardware_bom": bool(get_hardware_bom()),
        "hardware_inventory": bool(get_hardware_inventory_json()),
        "pre_week1_checklist": bool(get_pre_week1_checklist()),
        "roadmap_audit_patches": bool(get_roadmap_audit_patches()),
    }


def list_bom_items_to_buy() -> List[Dict[str, Any]]:
    """Return list of BOM items that are not yet in inventory (items to buy)."""
    bom = get_hardware_bom()
    if not bom:
        return []
    
    # Get inventory names (lowercase for comparison)
    inventory = list_hardware()
    inventory_names = {item.name.lower() for item in inventory}
    
    # Find BOM items not in inventory
    to_buy = []
    for category_name, category_data in bom.get("categories", {}).items():
        for item in category_data.get("items", []):
            if item["name"].lower() not in inventory_names:
                to_buy.append({
                    "name": item["name"],
                    "category": category_name.replace("_", " ").title(),
                    "priority": item.get("priority", "optional"),
                    "price_inr": item.get("price_inr", 0),
                    "phase_needed": item.get("phase_needed"),
                    "week_needed": item.get("week_needed"),
                    "description": item.get("description", ""),
                })
    
    # Sort by priority then phase
    priority_order = {"essential": 0, "recommended": 1, "optional": 2}
    to_buy.sort(key=lambda x: (priority_order.get(x["priority"], 3), x.get("phase_needed", 99)))
    
    return to_buy


# -----------------------------------------------------------------------------
# Backup & Restore
# -----------------------------------------------------------------------------

import json
from pathlib import Path


def backup_database_to_json(output_path: str | Path) -> str:
    """Export entire database to a JSON backup file.
    
    Args:
        output_path: Path for the backup file (e.g., "backup_2024-01-01.json")
    
    Returns:
        The absolute path of the created backup file.
    """
    backup_data = {
        "backup_timestamp": _utcnow().isoformat(),
        "version": "1.0",
        "phases": [],
        "certifications": [],
        "applications": [],
        "hardware": [],
    }
    
    with session_scope() as session:
        # Export Phases with nested Weeks, Days, Tasks, Resources
        phases = session.exec(select(Phase)).all()
        for phase in phases:
            phase_data = {
                "id": phase.id,
                "name": phase.name,
                "description": phase.description,
                "start_date": phase.start_date.isoformat() if phase.start_date else None,
                "end_date": phase.end_date.isoformat() if phase.end_date else None,
                "weeks": [],
                "projects": [],
                "metrics": [],
            }
            
            # Weeks
            weeks = session.exec(select(Week).where(Week.phase_id == phase.id)).all()
            for week in weeks:
                week_data = {
                    "id": week.id,
                    "number": week.number,
                    "focus": week.focus,
                    "start_date": week.start_date.isoformat() if week.start_date else None,
                    "end_date": week.end_date.isoformat() if week.end_date else None,
                    "status": week.status.value if week.status else None,
                    "days": [],
                    "tasks": [],
                    "resources": [],
                }
                
                # Days
                days = session.exec(select(DayPlan).where(DayPlan.week_id == week.id)).all()
                for day in days:
                    day_data = {
                        "id": day.id,
                        "number": day.number,
                        "focus": day.focus,
                        "scheduled_date": day.scheduled_date.isoformat() if day.scheduled_date else None,
                        "status": day.status.value if day.status else None,
                    }
                    week_data["days"].append(day_data)
                
                # Tasks
                tasks = session.exec(select(Task).where(Task.week_id == week.id)).all()
                for task in tasks:
                    task_data = {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value if task.status else None,
                        "estimated_hours": task.estimated_hours,
                        "actual_hours": task.actual_hours,
                        "ai_prompt": task.ai_prompt,
                        "day_id": task.day_id,
                        "hour_number": task.hour_number,
                        "total_work_seconds": task.total_work_seconds,
                        "total_break_seconds": task.total_break_seconds,
                        "total_pause_seconds": task.total_pause_seconds,
                    }
                    week_data["tasks"].append(task_data)
                
                # Resources
                resources = session.exec(select(Resource).where(Resource.week_id == week.id)).all()
                for resource in resources:
                    resource_data = {
                        "id": resource.id,
                        "title": resource.title,
                        "type": resource.type.value if resource.type else None,
                        "url": resource.url,
                        "notes": resource.notes,
                    }
                    week_data["resources"].append(resource_data)
                
                phase_data["weeks"].append(week_data)
            
            # Projects
            projects = session.exec(select(Project).where(Project.phase_id == phase.id)).all()
            for project in projects:
                project_data = {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status.value if project.status else None,
                    "repo_url": project.repo_url,
                    "due_date": project.due_date.isoformat() if project.due_date else None,
                }
                phase_data["projects"].append(project_data)
            
            # Metrics
            metrics = session.exec(select(Metric).where(Metric.phase_id == phase.id)).all()
            for metric in metrics:
                metric_data = {
                    "id": metric.id,
                    "metric_type": metric.metric_type,
                    "value": metric.value,
                    "unit": metric.unit,
                    "recorded_date": metric.recorded_date.isoformat() if metric.recorded_date else None,
                }
                phase_data["metrics"].append(metric_data)
            
            backup_data["phases"].append(phase_data)
        
        # Certifications
        certs = session.exec(select(Certification)).all()
        for cert in certs:
            cert_data = {
                "id": cert.id,
                "name": cert.name,
                "provider": cert.provider,
                "status": cert.status.value if cert.status else None,
                "progress": cert.progress,
                "due_date": cert.due_date.isoformat() if cert.due_date else None,
            }
            backup_data["certifications"].append(cert_data)
        
        # Applications
        apps = session.exec(select(Application)).all()
        for app in apps:
            app_data = {
                "id": app.id,
                "company": app.company,
                "role": app.role,
                "status": app.status.value if app.status else None,
                "date_applied": app.date_applied.isoformat() if app.date_applied else None,
                "next_action": app.next_action,
            }
            backup_data["applications"].append(app_data)
        
        # Hardware
        hardware = session.exec(select(HardwareItem)).all()
        for item in hardware:
            hw_data = {
                "id": item.id,
                "name": item.name,
                "category": item.category.value if item.category else None,
                "status": item.status.value if item.status else None,
                "quantity": item.quantity,
                "price_inr": item.price_inr,
                "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
                "notes": item.notes,
            }
            backup_data["hardware"].append(hw_data)
    
    # Write to file
    output_path = Path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Database backed up to {output_path}")
    return str(output_path.absolute())


def restore_database_from_json(backup_path: str | Path) -> dict:
    """Restore database from a JSON backup file.
    
    WARNING: This will overwrite existing data!
    
    Args:
        backup_path: Path to the backup file
    
    Returns:
        Summary of restored records
    """
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    with open(backup_path, "r", encoding="utf-8") as f:
        backup_data = json.load(f)
    
    summary = {
        "phases": 0,
        "weeks": 0,
        "days": 0,
        "tasks": 0,
        "resources": 0,
        "projects": 0,
        "metrics": 0,
        "certifications": 0,
        "applications": 0,
        "hardware": 0,
    }
    
    with session_scope() as session:
        # Restore phases and nested data
        for phase_data in backup_data.get("phases", []):
            phase = Phase(
                name=phase_data["name"],
                description=phase_data.get("description"),
                start_date=date.fromisoformat(phase_data["start_date"]) if phase_data.get("start_date") else None,
                end_date=date.fromisoformat(phase_data["end_date"]) if phase_data.get("end_date") else None,
            )
            session.add(phase)
            session.flush()
            summary["phases"] += 1
            
            for week_data in phase_data.get("weeks", []):
                week = Week(
                    number=week_data["number"],
                    focus=week_data.get("focus"),
                    status=TaskStatus(week_data["status"]) if week_data.get("status") else TaskStatus.PENDING,
                    phase_id=phase.id,
                    start_date=date.fromisoformat(week_data["start_date"]) if week_data.get("start_date") else None,
                    end_date=date.fromisoformat(week_data["end_date"]) if week_data.get("end_date") else None,
                )
                session.add(week)
                session.flush()
                summary["weeks"] += 1
                
                # Day ID mapping for tasks
                day_id_map = {}
                for day_data in week_data.get("days", []):
                    day = DayPlan(
                        number=day_data["number"],
                        focus=day_data.get("focus"),
                        scheduled_date=date.fromisoformat(day_data["scheduled_date"]) if day_data.get("scheduled_date") else None,
                        status=TaskStatus(day_data["status"]) if day_data.get("status") else TaskStatus.PENDING,
                        week_id=week.id,
                    )
                    session.add(day)
                    session.flush()
                    day_id_map[day_data["id"]] = day.id
                    summary["days"] += 1
                
                for task_data in week_data.get("tasks", []):
                    new_day_id = day_id_map.get(task_data.get("day_id")) if task_data.get("day_id") else None
                    task = Task(
                        title=task_data["title"],
                        description=task_data.get("description"),
                        status=TaskStatus(task_data["status"]) if task_data.get("status") else TaskStatus.PENDING,
                        estimated_hours=task_data.get("estimated_hours"),
                        actual_hours=task_data.get("actual_hours"),
                        ai_prompt=task_data.get("ai_prompt"),
                        week_id=week.id,
                        day_id=new_day_id,
                        hour_number=task_data.get("hour_number"),
                        total_work_seconds=task_data.get("total_work_seconds", 0),
                        total_break_seconds=task_data.get("total_break_seconds", 0),
                        total_pause_seconds=task_data.get("total_pause_seconds", 0),
                    )
                    session.add(task)
                    summary["tasks"] += 1
                
                for resource_data in week_data.get("resources", []):
                    resource = Resource(
                        title=resource_data["title"],
                        type=ResourceType(resource_data["type"]) if resource_data.get("type") else ResourceType.ARTICLE,
                        url=resource_data.get("url"),
                        notes=resource_data.get("notes"),
                        week_id=week.id,
                    )
                    session.add(resource)
                    summary["resources"] += 1
            
            for project_data in phase_data.get("projects", []):
                project = Project(
                    name=project_data["name"],
                    description=project_data.get("description"),
                    status=ProjectStatus(project_data["status"]) if project_data.get("status") else ProjectStatus.PLANNED,
                    repo_url=project_data.get("repo_url"),
                    due_date=date.fromisoformat(project_data["due_date"]) if project_data.get("due_date") else None,
                    phase_id=phase.id,
                )
                session.add(project)
                summary["projects"] += 1
            
            for metric_data in phase_data.get("metrics", []):
                metric = Metric(
                    metric_type=metric_data["metric_type"],
                    value=metric_data["value"],
                    unit=metric_data.get("unit"),
                    recorded_date=date.fromisoformat(metric_data["recorded_date"]) if metric_data.get("recorded_date") else None,
                    phase_id=phase.id,
                )
                session.add(metric)
                summary["metrics"] += 1
        
        # Certifications
        for cert_data in backup_data.get("certifications", []):
            cert = Certification(
                name=cert_data["name"],
                provider=cert_data.get("provider"),
                status=CertificationStatus(cert_data["status"]) if cert_data.get("status") else CertificationStatus.PLANNED,
                progress=cert_data.get("progress", 0.0),
                due_date=date.fromisoformat(cert_data["due_date"]) if cert_data.get("due_date") else None,
            )
            session.add(cert)
            summary["certifications"] += 1
        
        # Applications
        for app_data in backup_data.get("applications", []):
            app = Application(
                company=app_data["company"],
                role=app_data["role"],
                status=ApplicationStatus(app_data["status"]) if app_data.get("status") else ApplicationStatus.APPLIED,
                date_applied=date.fromisoformat(app_data["date_applied"]) if app_data.get("date_applied") else None,
                next_action=app_data.get("next_action"),
            )
            session.add(app)
            summary["applications"] += 1
        
        # Hardware
        for hw_data in backup_data.get("hardware", []):
            hw = HardwareItem(
                name=hw_data["name"],
                category=HardwareCategory(hw_data["category"]) if hw_data.get("category") else HardwareCategory.OTHER,
                status=HardwareStatus(hw_data["status"]) if hw_data.get("status") else HardwareStatus.AVAILABLE,
                quantity=hw_data.get("quantity", 1),
                price_inr=hw_data.get("price_inr"),
                purchase_date=date.fromisoformat(hw_data["purchase_date"]) if hw_data.get("purchase_date") else None,
                notes=hw_data.get("notes"),
            )
            session.add(hw)
            summary["hardware"] += 1
    
    logger.info(f"Database restored from {backup_path}: {summary}")
    return summary
