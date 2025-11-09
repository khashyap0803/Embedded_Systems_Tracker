"""High-level data helpers used by both the CLI and the forthcoming GUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
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


UNSET = object()

UTC = timezone.utc


def _utcnow() -> datetime:
    return datetime.now(UTC)


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
# Phase helpers
# -----------------------------------------------------------------------------

def list_phases() -> List[PhaseRecord]:
    with session_scope() as session:
        rows = session.exec(select(Phase).order_by(Phase.start_date)).all()
        now = _utcnow()
        return [_phase_to_record(session, row, now) for row in rows]


def create_phase(*, name: str, description: Optional[str], start_date: date, end_date: date) -> PhaseRecord:
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
        if start_date is not UNSET:
            phase.start_date = start_date
        if end_date is not UNSET:
            phase.end_date = end_date
        session.add(phase)
        session.flush()
        session.refresh(phase)
        return _phase_to_record(session, phase, _utcnow())


def delete_phase(phase_id: int) -> None:
    with session_scope() as session:
        phase = session.get(Phase, phase_id)
        if phase is None:
            raise ValueError(f"Phase {phase_id} not found")
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
    with session_scope() as session:
        week = session.get(Week, week_id)
        if week is None:
            raise ValueError(f"Week {week_id} not found")
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


def delete_day(day_id: int) -> None:
    with session_scope() as session:
        day = session.get(DayPlan, day_id)
        if day is None:
            raise ValueError(f"Day {day_id} not found")
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
) -> List[TaskRecord]:
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
        now = _utcnow()
        rows: List[TaskRecord] = []
        ordered = session.exec(
            statement.order_by(Week.number, DayPlan.number.nulls_last(), Task.hour_number.nulls_last(), Task.title)
        ).all()
        for task, week, phase, day in ordered:
            if only_open and task.status not in open_states:
                continue
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


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _seconds_between(start: Optional[datetime], end: datetime) -> int:
    end_utc = _ensure_utc(end)
    start_utc = _ensure_utc(start)
    if start_utc is None or end_utc is None:
        return 0
    return max(0, int((end_utc - start_utc).total_seconds()))


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
        day.status = TaskStatus.PENDING
        day.actual_start = None
        day.actual_end = None
        session.add(day)
        return
    child_statuses = [task.status for task in tasks]
    new_status = _derive_container_status(child_statuses)
    day.status = new_status
    if new_status == TaskStatus.PENDING:
        day.actual_start = None
        day.actual_end = None
    else:
        start_candidates = [task.first_started_at for task in tasks if task.first_started_at]
        if start_candidates:
            earliest = min(start_candidates)
            day.actual_start = earliest if day.actual_start is None else min(day.actual_start, earliest)
        if new_status == TaskStatus.COMPLETED:
            end_candidates = [task.completed_at for task in tasks if task.completed_at]
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
            start_candidates = [day.actual_start for day in days if day.actual_start]
            if not start_candidates:
                tasks = session.exec(select(Task).where(Task.week_id == week.id)).all()
                start_candidates = [task.first_started_at for task in tasks if task.first_started_at]
            if start_candidates:
                earliest = min(start_candidates)
                week.actual_start = earliest if week.actual_start is None else min(week.actual_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = [day.actual_end for day in days if day.actual_end]
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
            start_candidates = [task.first_started_at for task in tasks if task.first_started_at]
            if start_candidates:
                earliest = min(start_candidates)
                week.actual_start = earliest if week.actual_start is None else min(week.actual_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = [task.completed_at for task in tasks if task.completed_at]
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
            start_candidates = [week.actual_start for week in weeks if week.actual_start]
            if not start_candidates:
                tasks = session.exec(
                    select(Task)
                    .join(Week, Task.week_id == Week.id)
                    .where(Week.phase_id == phase.id)
                ).all()
                start_candidates = [task.first_started_at for task in tasks if task.first_started_at]
            if start_candidates:
                earliest = min(start_candidates)
                phase.actual_start = earliest if phase.actual_start is None else min(phase.actual_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = [week.actual_end for week in weeks if week.actual_end]
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
            start_candidates = [task.first_started_at for task in tasks if task.first_started_at]
            if start_candidates:
                earliest = min(start_candidates)
                phase.actual_start = earliest if phase.actual_start is None else min(phase.actual_start, earliest)
            if new_status == TaskStatus.COMPLETED:
                end_candidates = [task.completed_at for task in tasks if task.completed_at]
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
