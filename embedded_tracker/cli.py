"""Command line entry points for the Embedded Tracker."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from sqlmodel import select

from .db import ensure_seed_data, init_db, session_scope
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

console = Console()

UTC = timezone.utc


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _current_work_hours(task: Task) -> float:
    """Return the hours logged for a task, including active sessions."""

    seconds = task.total_work_seconds or 0
    if task.status == TaskStatus.WORKING:
        last_start = _ensure_utc(task.last_work_started_at)
        if last_start:
            seconds += max(0, int((_utcnow() - last_start).total_seconds()))
    return round(seconds / 3600, 2)


def list_tasks(
    week: Optional[int] = None,
    phase: Optional[str] = None,
    only_open: bool = False,
) -> None:
    """Display tasks according to the current filter criteria."""

    open_states = {TaskStatus.PENDING, TaskStatus.WORKING, TaskStatus.BREAK, TaskStatus.PAUSED}

    with session_scope() as session:
        statement = (
            select(Task, Week, Phase, DayPlan)
            .join(Week, Task.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
            .join(DayPlan, Task.day_id == DayPlan.id, isouter=True)
        )
        if week is not None:
            statement = statement.where(Week.number == week)

        rows = []
        for task, week_obj, phase_obj, day_obj in session.exec(statement).all():
            if phase and phase.lower() not in phase_obj.name.lower():
                continue
            if only_open and task.status not in open_states:
                continue

            rows.append(
                {
                    "phase": phase_obj.name,
                    "week": week_obj.number,
                    "day": day_obj.number if day_obj else "-",
                    "hour": task.hour_number if task.hour_number is not None else "-",
                    "title": task.title,
                    "status": task.status.value,
                    "est_hours": task.estimated_hours or 0.0,
                    "logged_hours": _current_work_hours(task),
                    "prompt": task.ai_prompt or "",
                }
            )

    if not rows:
        console.print("[yellow]No tasks found with the given filters.[/yellow]")
        return

    table = Table(title="Roadmap Tasks", show_lines=True)
    table.add_column("Phase")
    table.add_column("Week", justify="center")
    table.add_column("Day", justify="center")
    table.add_column("Hour", justify="center")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Est. Hours", justify="right")
    table.add_column("Logged Hours", justify="right")
    table.add_column("AI Prompt")

    for row in rows:
        table.add_row(
            row["phase"],
            str(row["week"]),
            str(row["day"]),
            str(row["hour"]),
            row["title"],
            row["status"],
            f"{row['est_hours']:.1f}",
            f"{row['logged_hours']:.2f}",
            row["prompt"],
        )

    console.print(table)


def today() -> None:
    """Show tasks whose week contains today's date."""

    today_date = date.today()
    with session_scope() as session:
        statement = (
            select(Task, Week, Phase, DayPlan)
            .join(Week, Task.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
            .join(DayPlan, Task.day_id == DayPlan.id, isouter=True)
            .where(Week.start_date <= today_date)
            .where(Week.end_date >= today_date)
        )
        rows = []
        for task, week_obj, phase_obj, day_obj in session.exec(statement).all():
            if day_obj and day_obj.scheduled_date != today_date:
                continue
            rows.append(
                {
                    "phase": phase_obj.name,
                    "week": week_obj.number,
                    "day": day_obj.number if day_obj else "-",
                    "hour": task.hour_number if task.hour_number is not None else "-",
                    "title": task.title,
                    "status": task.status.value,
                    "logged_hours": _current_work_hours(task),
                }
            )

    if not rows:
        console.print("[cyan]No tasks scheduled for the current week.[/cyan]")
        return

    table = Table(title=f"Tasks for the week of {today_date.isoformat()}", show_lines=True)
    table.add_column("Phase")
    table.add_column("Week", justify="center")
    table.add_column("Day", justify="center")
    table.add_column("Hour", justify="center")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Logged Hours", justify="right")

    for row in rows:
        table.add_row(
            row["phase"],
            str(row["week"]),
            str(row["day"]),
            str(row["hour"]),
            row["title"],
            row["status"],
            f"{row['logged_hours']:.2f}",
        )

    console.print(table)


def list_resources(
    week: Optional[int] = None,
    resource_type: Optional[ResourceType] = None,
) -> None:
    """Display study resources."""

    with session_scope() as session:
        statement = (
            select(Resource, Week, Phase)
            .join(Week, Resource.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
        )
        if week is not None:
            statement = statement.where(Week.number == week)

        rows = []
        for resource, week_obj, phase_obj in session.exec(statement).all():
            if resource_type and resource.type != resource_type:
                continue

            rows.append(
                {
                    "title": resource.title,
                    "type": resource.type.value,
                    "week": week_obj.number,
                    "phase": phase_obj.name,
                    "url": resource.url or "",
                }
            )

    if not rows:
        console.print("[yellow]No resources matched the filters.[/yellow]")
        return

    table = Table(title="Study Resources", show_lines=True)
    table.add_column("Phase")
    table.add_column("Week", justify="center")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("URL")

    for row in rows:
        table.add_row(
            row["phase"],
            str(row["week"]),
            row["title"],
            row["type"],
            row["url"],
        )

    console.print(table)


def list_projects(
    status: Optional[ProjectStatus] = None,
    phase: Optional[str] = None,
) -> None:
    """Display portfolio projects."""

    with session_scope() as session:
        statement = select(Project, Phase).join(Phase, Project.phase_id == Phase.id, isouter=True)
        rows = []
        for project, phase_obj in session.exec(statement).all():
            phase_name = phase_obj.name if phase_obj else "Unassigned"
            if phase and phase.lower() not in phase_name.lower():
                continue
            if status and project.status != status:
                continue

            rows.append(
                {
                    "name": project.name,
                    "status": project.status.value,
                    "phase": phase_name,
                    "repo_url": project.repo_url or "",
                    "due_date": project.due_date.isoformat() if project.due_date else "-",
                }
            )

    if not rows:
        console.print("[yellow]No projects matched the filters.[/yellow]")
        return

    table = Table(title="Portfolio Projects", show_lines=True)
    table.add_column("Phase")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Due Date")
    table.add_column("Repository")

    for row in rows:
        table.add_row(
            row["phase"],
            row["name"],
            row["status"],
            row["due_date"],
            row["repo_url"],
        )

    console.print(table)


def list_certifications(status: Optional[CertificationStatus] = None) -> None:
    """Display certification roadmap."""

    with session_scope() as session:
        fetched: List[Certification] = session.exec(select(Certification)).all()
        rows = []
        for cert in fetched:
            if status and cert.status != status:
                continue

            rows.append(
                {
                    "name": cert.name,
                    "provider": cert.provider or "",
                    "status": cert.status.value,
                    "progress": f"{cert.progress * 100:.0f}%",
                    "due_date": cert.due_date.isoformat() if cert.due_date else "-",
                }
            )

    if not rows:
        console.print("[yellow]No certifications matched the filters.[/yellow]")
        return

    table = Table(title="Certifications", show_lines=True)
    table.add_column("Name")
    table.add_column("Provider")
    table.add_column("Status")
    table.add_column("Progress")
    table.add_column("Due Date")

    for row in rows:
        table.add_row(
            row["name"],
            row["provider"],
            row["status"],
            row["progress"],
            row["due_date"],
        )

    console.print(table)


def list_applications(status: Optional[ApplicationStatus] = None) -> None:
    """Display job applications."""

    with session_scope() as session:
        fetched: List[Application] = session.exec(select(Application)).all()
        rows = []
        for application in fetched:
            if status and application.status != status:
                continue

            rows.append(
                {
                    "company": application.company,
                    "role": application.role,
                    "status": application.status.value,
                    "date": application.date_applied.isoformat()
                    if application.date_applied
                    else "-",
                    "next": application.next_action or "",
                }
            )

    if not rows:
        console.print("[yellow]No applications matched the filters.[/yellow]")
        return

    table = Table(title="Job Applications", show_lines=True)
    table.add_column("Company")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Applied")
    table.add_column("Next Action")

    for row in rows:
        table.add_row(row["company"], row["role"], row["status"], row["date"], row["next"])

    console.print(table)


def list_metrics(metric_type: Optional[str] = None) -> None:
    """Display metrics such as hours logged or quiz scores."""

    with session_scope() as session:
        statement = select(Metric, Phase).join(Phase, Metric.phase_id == Phase.id, isouter=True)
        rows = []
        for metric, phase_obj in session.exec(statement).all():
            if metric_type and metric.metric_type.lower() != metric_type.lower():
                continue

            rows.append(
                {
                    "type": metric.metric_type,
                    "value": metric.value,
                    "unit": metric.unit or "",
                    "date": metric.recorded_date.isoformat(),
                    "phase": phase_obj.name if phase_obj else "-",
                }
            )

    if not rows:
        console.print("[yellow]No metrics found for the provided filter.[/yellow]")
        return

    table = Table(title="Metrics", show_lines=True)
    table.add_column("Date")
    table.add_column("Type")
    table.add_column("Value")
    table.add_column("Unit")
    table.add_column("Phase")

    for row in rows:
        table.add_row(
            row["date"],
            row["type"],
            f"{row['value']:.2f}",
            row["unit"],
            row["phase"],
        )

    console.print(table)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Embedded roadmap assistant CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List roadmap tasks")
    list_parser.add_argument("--week", type=int, help="Week number to filter by")
    list_parser.add_argument("--phase", type=str, help="Phase name keyword to filter by")
    list_parser.add_argument("--only-open", action="store_true", help="Show only open tasks")

    subparsers.add_parser("today", help="Show tasks scheduled for the current week")

    resources_parser = subparsers.add_parser("resources", help="List study resources")
    resources_parser.add_argument("--week", type=int, help="Week number to filter by")
    resources_parser.add_argument(
        "--type",
        choices=[member.value for member in ResourceType],
        help="Resource type to filter by",
    )

    projects_parser = subparsers.add_parser("projects", help="List portfolio projects")
    projects_parser.add_argument(
        "--status",
        choices=[member.value for member in ProjectStatus],
        help="Filter projects by status",
    )
    projects_parser.add_argument("--phase", help="Phase name keyword to filter by")

    certs_parser = subparsers.add_parser("certifications", help="List certifications")
    certs_parser.add_argument(
        "--status",
        choices=[member.value for member in CertificationStatus],
        help="Filter certifications by status",
    )

    applications_parser = subparsers.add_parser("applications", help="List job applications")
    applications_parser.add_argument(
        "--status",
        choices=[member.value for member in ApplicationStatus],
        help="Filter applications by status",
    )

    metrics_parser = subparsers.add_parser("metrics", help="List metrics")
    metrics_parser.add_argument("--metric-type", help="Filter metrics by type")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    init_db()
    ensure_seed_data()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        list_tasks(week=args.week, phase=args.phase, only_open=args.only_open)
    elif args.command == "today":
        today()
    elif args.command == "resources":
        r_type = ResourceType(args.type) if args.type else None
        list_resources(week=args.week, resource_type=r_type)
    elif args.command == "projects":
        status = ProjectStatus(args.status) if args.status else None
        list_projects(status=status, phase=args.phase)
    elif args.command == "certifications":
        status = CertificationStatus(args.status) if args.status else None
        list_certifications(status=status)
    elif args.command == "applications":
        status = ApplicationStatus(args.status) if args.status else None
        list_applications(status=status)
    elif args.command == "metrics":
        list_metrics(metric_type=args.metric_type)
    else:
        parser.error("Unknown command")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
