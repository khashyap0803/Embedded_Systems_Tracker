"""Reusable seeding helpers for the Embedded Tracker."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, Type, TypeVar

from sqlmodel import select

from .db import init_db, session_scope
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

__all__ = ["seed_from_payload", "seed_from_file"]

E = TypeVar("E", bound=Enum)


def normalise_date(value: str | None) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(value)


def coerce_enum(enum_cls: Type[E], raw: Any, default: E) -> E:
    if isinstance(raw, enum_cls):
        return raw
    if isinstance(raw, str):
        candidate = raw.replace(" ", "_").lower()
        try:
            return enum_cls(candidate)  # type: ignore[arg-type]
        except ValueError:
            pass
    return default


def upsert_phase(session, phase_payload: Dict[str, Any]) -> Phase:
    phase = session.exec(select(Phase).where(Phase.name == phase_payload["name"])).first()
    if phase is None:
        phase = Phase(
            name=phase_payload["name"],
            description=phase_payload.get("description"),
            start_date=normalise_date(phase_payload.get("start_date")),  # Optional now
            end_date=normalise_date(phase_payload.get("end_date")),  # Optional now
        )
        session.add(phase)
        session.flush()
    else:
        phase.description = phase_payload.get("description", phase.description)
        if "start_date" in phase_payload:
            phase.start_date = normalise_date(phase_payload.get("start_date"))
        if "end_date" in phase_payload:
            phase.end_date = normalise_date(phase_payload.get("end_date"))
    phase.status = coerce_enum(TaskStatus, phase_payload.get("status"), TaskStatus.PENDING)
    return phase


def upsert_week(session, phase: Phase, week_payload: Dict[str, Any]) -> Week:
    week = (
        session.exec(
            select(Week)
            .where(Week.phase_id == phase.id)
            .where(Week.number == week_payload["number"])
        ).first()
    )
    if week is None:
        week = Week(
            number=week_payload["number"],
            start_date=normalise_date(week_payload.get("start_date")),  # Optional now
            end_date=normalise_date(week_payload.get("end_date")),  # Optional now
            focus=week_payload.get("focus"),
            phase_id=phase.id,
        )
        session.add(week)
        session.flush()
    else:
        if "start_date" in week_payload:
            week.start_date = normalise_date(week_payload.get("start_date"))
        if "end_date" in week_payload:
            week.end_date = normalise_date(week_payload.get("end_date"))
        week.focus = week_payload.get("focus", week.focus)
    week.status = coerce_enum(TaskStatus, week_payload.get("status"), TaskStatus.PENDING)
    return week


def upsert_day(session, week: Week, day_payload: Dict[str, Any]) -> DayPlan:
    number = day_payload["number"]
    day = (
        session.exec(
            select(DayPlan)
            .where(DayPlan.week_id == week.id)
            .where(DayPlan.number == number)
        ).first()
    )
    if day is None:
        day = DayPlan(
            number=number,
            scheduled_date=normalise_date(day_payload.get("scheduled_date")) or week.start_date,
            focus=day_payload.get("focus"),
            notes=day_payload.get("notes"),
            week_id=week.id,
        )
        session.add(day)
        session.flush()
    else:
        day.scheduled_date = normalise_date(day_payload.get("scheduled_date")) or day.scheduled_date
        day.focus = day_payload.get("focus", day.focus)
        day.notes = day_payload.get("notes", day.notes)
    day.status = coerce_enum(TaskStatus, day_payload.get("status"), TaskStatus.PENDING)
    return day


def upsert_task(
    session,
    week: Week,
    task_payload: Dict[str, Any],
    *,
    day: DayPlan | None = None,
    existing_tasks: List[Task] | None = None,
) -> Task:
    title = task_payload["title"]
    hour_number = task_payload.get("hour_number")

    task = None
    if existing_tasks is not None:
        # Filter in memory
        candidates = [t for t in existing_tasks if t.week_id == week.id]
        if day is not None:
            candidates = [t for t in candidates if t.day_id == day.id]
        
        if hour_number is not None:
            candidates = [t for t in candidates if t.hour_number == hour_number]
        else:
            candidates = [t for t in candidates if t.title == title]
        
        if candidates:
            task = candidates[0]

    if task is None and existing_tasks is None:
        # Fallback to DB query if no cache provided
        query = select(Task).where(Task.week_id == week.id)
        if day is not None:
            query = query.where(Task.day_id == day.id)
        if hour_number is not None:
            query = query.where(Task.hour_number == hour_number)
        else:
            query = query.where(Task.title == title)
        task = session.exec(query).first()
    raw_status = task_payload.get("status", "pending")
    status = coerce_enum(TaskStatus, raw_status, TaskStatus.PENDING)
    if task is None:
        task = Task(
            title=title,
            description=task_payload.get("description"),
            status=status,
            estimated_hours=task_payload.get("estimated_hours"),
            actual_hours=task_payload.get("actual_hours"),
            ai_prompt=task_payload.get("ai_prompt"),
            week_id=week.id,
            day_id=day.id if day else None,
            hour_number=hour_number,
        )
        session.add(task)
    else:
        task.description = task_payload.get("description", task.description)
        task.status = status
        task.estimated_hours = task_payload.get("estimated_hours", task.estimated_hours)
        task.actual_hours = task_payload.get("actual_hours", task.actual_hours)
        task.ai_prompt = task_payload.get("ai_prompt", task.ai_prompt)
        if day:
            task.day_id = day.id
        if hour_number is not None:
            task.hour_number = hour_number
    if task_payload.get("estimated_minutes") and not task_payload.get("estimated_hours"):
        task.estimated_hours = float(task_payload["estimated_minutes"]) / 60.0
    if task_payload.get("status_updated_at"):
        raw = task_payload["status_updated_at"]
        if isinstance(raw, str):
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            task.status_updated_at = parsed
        else:
            task.status_updated_at = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    else:
        task.status_updated_at = datetime.now(timezone.utc)
    return task


def upsert_resource(session, week: Week, resource_payload: Dict[str, Any]) -> Resource:
    title = resource_payload["title"]
    resource = (
        session.exec(
            select(Resource)
            .where(Resource.week_id == week.id)
            .where(Resource.title == title)
        ).first()
    )

    resource_type = coerce_enum(ResourceType, resource_payload.get("type"), ResourceType.OTHER)
    if resource is None:
        resource = Resource(
            title=title,
            type=resource_type,
            notes=resource_payload.get("notes"),
            url=resource_payload.get("url"),
            week_id=week.id,
        )
        session.add(resource)
    else:
        resource.type = resource_type
        resource.notes = resource_payload.get("notes", resource.notes)
        resource.url = resource_payload.get("url", resource.url)
    return resource


def upsert_project(session, phase: Phase, project_payload: Dict[str, Any]) -> Project:
    name = project_payload["name"]
    project = session.exec(select(Project).where(Project.name == name)).first()
    status = coerce_enum(ProjectStatus, project_payload.get("status"), ProjectStatus.PLANNED)
    start_date = normalise_date(project_payload.get("start_date"))
    due_date = normalise_date(project_payload.get("due_date"))
    if project is None:
        project = Project(
            name=name,
            description=project_payload.get("description"),
            repo_url=project_payload.get("repo_url"),
            demo_url=project_payload.get("demo_url"),
            start_date=start_date,
            due_date=due_date,
            phase_id=phase.id,
            status=status,
        )
        session.add(project)
    else:
        project.description = project_payload.get("description", project.description)
        project.repo_url = project_payload.get("repo_url", project.repo_url)
        project.demo_url = project_payload.get("demo_url", project.demo_url)
        if start_date is not None:
            project.start_date = start_date
        if due_date is not None:
            project.due_date = due_date
        project.phase_id = phase.id
        project.status = status
    return project


def upsert_metric(session, phase: Phase | None, metric_payload: Dict[str, Any]) -> Metric:
    metric = Metric(
        metric_type=metric_payload["metric_type"],
        value=metric_payload.get("value", 0.0),
        unit=metric_payload.get("unit"),
        recorded_date=normalise_date(metric_payload.get("recorded_date")) or date.today(),
        phase_id=phase.id if phase else None,
    )
    session.add(metric)
    return metric


def upsert_certification(session, phase: Phase | None, cert_payload: Dict[str, Any]) -> Certification:
    name = cert_payload["name"]
    cert = session.exec(select(Certification).where(Certification.name == name)).first()
    status = coerce_enum(
        CertificationStatus,
        cert_payload.get("status"),
        CertificationStatus.PLANNED,
    )
    due_date = normalise_date(cert_payload.get("due_date"))
    completion_date = normalise_date(cert_payload.get("completion_date"))
    if cert is None:
        cert = Certification(
            name=name,
            provider=cert_payload.get("provider"),
            due_date=due_date,
            status=status,
            completion_date=completion_date,
            credential_url=cert_payload.get("credential_url"),
            progress=cert_payload.get("progress", 0.0),
            phase_id=phase.id if phase else None,
        )
        session.add(cert)
    else:
        cert.provider = cert_payload.get("provider", cert.provider)
        if due_date is not None:
            cert.due_date = due_date
        cert.status = status
        if completion_date is not None:
            cert.completion_date = completion_date
        cert.credential_url = cert_payload.get("credential_url", cert.credential_url)
        cert.progress = cert_payload.get("progress", cert.progress)
        cert.phase_id = phase.id if phase else None
    return cert


def upsert_application(session, application_payload: Dict[str, Any]) -> Application:
    company = application_payload["company"]
    role = application_payload.get("role")
    application = (
        session.exec(
            select(Application)
            .where(Application.company == company)
            .where(Application.role == role)
        ).first()
    )
    status = coerce_enum(
        ApplicationStatus,
        application_payload.get("status"),
        ApplicationStatus.DRAFT,
    )
    date_applied = normalise_date(application_payload.get("date_applied"))
    if application is None:
        application = Application(
            company=company,
            role=role,
            status=status,
            source=application_payload.get("source"),
            date_applied=date_applied,
            next_action=application_payload.get("next_action"),
            notes=application_payload.get("notes"),
        )
        session.add(application)
    else:
        application.status = status
        application.source = application_payload.get("source", application.source)
        if date_applied is not None:
            application.date_applied = date_applied
        application.next_action = application_payload.get("next_action", application.next_action)
        application.notes = application_payload.get("notes", application.notes)
    return application


def _iterate(values: Iterable[Dict[str, Any]] | None) -> Iterable[Dict[str, Any]]:
    if values is None:
        return []
    return values


def seed_from_payload(payload: Dict[str, Any]) -> int:
    init_db()
    phases = payload.get("phases", [])
    if not phases:
        raise ValueError("Seed file must contain at least one phase entry")

    with session_scope() as session:
        for phase_payload in phases:
            phase = upsert_phase(session, phase_payload)
            for week_payload in _iterate(phase_payload.get("weeks")):
                week = upsert_week(session, phase, week_payload)
                # Pre-fetch tasks to avoid N+1 queries during upsert
                week_tasks = session.exec(select(Task).where(Task.week_id == week.id)).all()
                if week.status is None:
                    week.status = TaskStatus.PENDING
                days_payload = list(_iterate(week_payload.get("days")))
                # Build mapping of JSON day IDs to database day objects
                json_day_id_to_db_day: Dict[int, DayPlan] = {}
                if days_payload:
                    for day_payload in days_payload:
                        day = upsert_day(session, week, day_payload)
                        if day.status is None:
                            day.status = TaskStatus.PENDING
                        # Map JSON day ID to database day object
                        json_day_id = day_payload.get("id")
                        if json_day_id is not None:
                            json_day_id_to_db_day[json_day_id] = day
                        for hour_payload in _iterate(day_payload.get("hours")):
                            upsert_task(session, week, hour_payload, day=day, existing_tasks=week_tasks)
                
                # Process week.tasks with proper day mapping
                for task_payload in _iterate(week_payload.get("tasks")):
                    task_day = None
                    task_day_id = task_payload.get("day_id")
                    if task_day_id is not None and task_day_id in json_day_id_to_db_day:
                        task_day = json_day_id_to_db_day[task_day_id]
                    upsert_task(session, week, task_payload, day=task_day, existing_tasks=week_tasks)
                for resource_payload in _iterate(week_payload.get("resources")):
                    upsert_resource(session, week, resource_payload)

            for project_payload in _iterate(phase_payload.get("projects")):
                upsert_project(session, phase, project_payload)

            for metric_payload in _iterate(phase_payload.get("metrics")):
                upsert_metric(session, phase, metric_payload)

            for cert_payload in _iterate(phase_payload.get("certifications")):
                upsert_certification(session, phase, cert_payload)

        for cert_payload in _iterate(payload.get("certifications")):
            upsert_certification(session, None, cert_payload)

        for application_payload in _iterate(payload.get("applications")):
            upsert_application(session, application_payload)

        for metric_payload in _iterate(payload.get("metrics")):
            upsert_metric(session, None, metric_payload)

    return len(phases)


def seed_from_file(seed_path: Path) -> int:
    if not seed_path.exists():
        raise FileNotFoundError(f"Seed file not found: {seed_path}")
    with seed_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return seed_from_payload(payload)
