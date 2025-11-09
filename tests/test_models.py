"""Minimal smoke tests for model behaviour."""

from datetime import date

from embedded_tracker.models import (
    Project,
    ProjectStatus,
    Resource,
    ResourceType,
    Task,
    TaskStatus,
    Week,
)


def test_task_default_state() -> None:
    week = Week(number=1, start_date=date.today(), end_date=date.today(), phase_id=42)
    task = Task(title="Sample", week_id=1)

    assert task.status is TaskStatus.PENDING
    assert task.week_id == 1


def test_resource_defaults() -> None:
    week = Week(number=1, start_date=date.today(), end_date=date.today(), phase_id=5)
    resource = Resource(title="Lecture", week_id=1)

    assert resource.type is ResourceType.OTHER


def test_project_status_override() -> None:
    project = Project(name="Voltage Divider", status=ProjectStatus.IN_PROGRESS)

    assert project.status is ProjectStatus.IN_PROGRESS
