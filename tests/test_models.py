"""Minimal smoke tests for model behaviour."""

from embedded_tracker.models import (
    Project,
    ProjectStatus,
    Resource,
    ResourceType,
    Task,
    TaskStatus,
)


def test_task_default_state() -> None:
    task = Task(title="Sample", week_id=1)

    assert task.status is TaskStatus.PENDING
    assert task.week_id == 1


def test_resource_defaults() -> None:
    resource = Resource(title="Lecture", week_id=1)

    assert resource.type is ResourceType.OTHER


def test_project_status_override() -> None:
    project = Project(name="Voltage Divider", status=ProjectStatus.IN_PROGRESS)

    assert project.status is ProjectStatus.IN_PROGRESS
