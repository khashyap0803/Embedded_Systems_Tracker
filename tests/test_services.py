"""Comprehensive tests for the services layer."""

from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import SQLModel, create_engine

from embedded_tracker.models import (
    TaskStatus,
    ProjectStatus,
    ResourceType,
)
from embedded_tracker import services


# Use an in-memory database for tests
@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Create a temporary database for each test."""
    db_path = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    # Patch the engine used by the services
    import embedded_tracker.db as db_module
    monkeypatch.setattr(db_module, "_ENGINE", test_engine)
    
    # Create tables
    SQLModel.metadata.create_all(test_engine)
    
    yield test_engine
    
    # Cleanup
    test_engine.dispose()


class TestPhaseOperations:
    """Tests for Phase CRUD operations."""

    def test_create_phase(self):
        """Test creating a phase."""
        phase = services.create_phase(
            name="Test Phase",
            description="A test phase",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        
        assert phase.name == "Test Phase"
        assert phase.description == "A test phase"
        assert phase.start_date == date(2025, 1, 1)
        assert phase.end_date == date(2025, 3, 31)
        assert phase.status == TaskStatus.PENDING

    def test_create_phase_invalid_date_range(self):
        """Test that creating a phase with end_date before start_date raises error."""
        with pytest.raises(ValueError, match="start_date.*cannot be after end_date"):
            services.create_phase(
                name="Invalid Phase",
                description="This should fail",
                start_date=date(2025, 6, 1),
                end_date=date(2025, 1, 1),
            )

    def test_list_phases(self):
        """Test listing phases."""
        # Create two phases
        services.create_phase(
            name="Phase 1",
            description="First",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        services.create_phase(
            name="Phase 2",
            description="Second",
            start_date=date(2025, 4, 1),
            end_date=date(2025, 6, 30),
        )
        
        phases = services.list_phases()
        assert len(phases) == 2
        assert phases[0].name == "Phase 1"
        assert phases[1].name == "Phase 2"

    def test_update_phase(self):
        """Test updating a phase."""
        phase = services.create_phase(
            name="Original Name",
            description="Original desc",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        
        updated = services.update_phase(
            phase.id,
            name="Updated Name",
            description="Updated desc",
        )
        
        assert updated.name == "Updated Name"
        assert updated.description == "Updated desc"
        # Unchanged fields should remain
        assert updated.start_date == date(2025, 1, 1)

    def test_delete_phase_cascades(self):
        """Test that deleting a phase cascades to related entities."""
        # Create a phase with week, day, task, resource, project
        phase = services.create_phase(
            name="Phase to Delete",
            description="Will be deleted",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        
        week = services.create_week(
            number=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            focus="Test week",
            phase_id=phase.id,
        )
        
        day = services.create_day(
            number=1,
            scheduled_date=date(2025, 1, 1),
            focus="Test day",
            notes=None,
            week_id=week.id,
        )
        
        _task = services.create_task(
            title="Test Task",
            description="A task",
            week_id=week.id,
            day_id=day.id,
            hour_number=1,
            estimated_hours=1.0,
            actual_hours=None,
            ai_prompt=None,
        )
        
        _resource = services.create_resource(
            title="Test Resource",
            type=ResourceType.ARTICLE,
            url="https://example.com",
            notes=None,
            week_id=week.id,
        )
        
        _project = services.create_project(
            name="Test Project",
            description="A project",
            status=ProjectStatus.PLANNED,
            phase_id=phase.id,
            repo_url=None,
            demo_url=None,
            start_date=None,
            due_date=None,
        )
        
        # Delete the phase
        services.delete_phase(phase.id)
        
        # Verify everything is deleted
        assert len(services.list_phases()) == 0
        assert len(services.list_weeks()) == 0
        assert len(services.list_days()) == 0
        assert len(services.list_tasks()) == 0
        assert len(services.list_resources()) == 0
        assert len(services.list_projects()) == 0


class TestWeekOperations:
    """Tests for Week CRUD operations."""

    def test_create_week(self):
        """Test creating a week."""
        phase = services.create_phase(
            name="Test Phase",
            description=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        
        week = services.create_week(
            number=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            focus="Week 1 focus",
            phase_id=phase.id,
        )
        
        assert week.number == 1
        assert week.focus == "Week 1 focus"
        assert week.phase_id == phase.id

    def test_create_week_invalid_date_range(self):
        """Test that creating a week with invalid date range raises error."""
        phase = services.create_phase(
            name="Test Phase",
            description=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        
        with pytest.raises(ValueError, match="start_date.*cannot be after end_date"):
            services.create_week(
                number=1,
                start_date=date(2025, 1, 7),
                end_date=date(2025, 1, 1),
                focus="Invalid week",
                phase_id=phase.id,
            )


class TestTaskStatusTransitions:
    """Tests for task status transitions and timer logic."""

    def test_task_status_pending_to_working(self):
        """Test transitioning from PENDING to WORKING."""
        phase = services.create_phase(
            name="Test Phase",
            description=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        week = services.create_week(
            number=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            focus=None,
            phase_id=phase.id,
        )
        day = services.create_day(
            number=1,
            scheduled_date=date(2025, 1, 1),
            focus=None,
            notes=None,
            week_id=week.id,
        )
        task = services.create_task(
            title="Test Task",
            description=None,
            week_id=week.id,
            day_id=day.id,
            hour_number=1,
            estimated_hours=1.0,
            actual_hours=None,
            ai_prompt=None,
        )
        
        # Transition to WORKING
        updated = services.update_task_status(task.id, TaskStatus.WORKING)
        
        assert updated.status == TaskStatus.WORKING
        assert updated.first_started_at is not None
        assert updated.is_running is True

    def test_task_status_working_to_completed(self):
        """Test transitioning from WORKING to COMPLETED."""
        phase = services.create_phase(
            name="Test Phase",
            description=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        week = services.create_week(
            number=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            focus=None,
            phase_id=phase.id,
        )
        day = services.create_day(
            number=1,
            scheduled_date=date(2025, 1, 1),
            focus=None,
            notes=None,
            week_id=week.id,
        )
        task = services.create_task(
            title="Test Task",
            description=None,
            week_id=week.id,
            day_id=day.id,
            hour_number=1,
            estimated_hours=1.0,
            actual_hours=None,
            ai_prompt=None,
        )
        
        # Start working then complete
        services.update_task_status(task.id, TaskStatus.WORKING)
        updated = services.update_task_status(task.id, TaskStatus.COMPLETED)
        
        assert updated.status == TaskStatus.COMPLETED
        assert updated.completed_at is not None
        assert updated.is_running is False


class TestContainerStatusRollup:
    """Tests for status roll-up from tasks to days/weeks/phases."""

    def test_day_status_updates_when_task_completes(self):
        """Test that day status updates when all tasks complete."""
        phase = services.create_phase(
            name="Test Phase",
            description=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        week = services.create_week(
            number=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            focus=None,
            phase_id=phase.id,
        )
        day = services.create_day(
            number=1,
            scheduled_date=date(2025, 1, 1),
            focus=None,
            notes=None,
            week_id=week.id,
        )
        task1 = services.create_task(
            title="Task 1",
            description=None,
            week_id=week.id,
            day_id=day.id,
            hour_number=1,
            estimated_hours=1.0,
            actual_hours=None,
            ai_prompt=None,
        )
        task2 = services.create_task(
            title="Task 2",
            description=None,
            week_id=week.id,
            day_id=day.id,
            hour_number=2,
            estimated_hours=1.0,
            actual_hours=None,
            ai_prompt=None,
        )
        
        # Complete first task
        services.update_task_status(task1.id, TaskStatus.COMPLETED)
        
        # Day should not be complete yet
        days = services.list_days()
        assert days[0].status != TaskStatus.COMPLETED
        
        # Complete second task
        services.update_task_status(task2.id, TaskStatus.COMPLETED)
        
        # Now day should be complete
        days = services.list_days()
        assert days[0].status == TaskStatus.COMPLETED


class TestDateValidation:
    """Tests for date validation in various entities."""

    def test_phase_date_validation(self):
        """Test phase date validation."""
        with pytest.raises(ValueError):
            services.create_phase(
                name="Invalid",
                description=None,
                start_date=date(2025, 12, 31),
                end_date=date(2025, 1, 1),
            )

    def test_week_date_validation(self):
        """Test week date validation."""
        phase = services.create_phase(
            name="Valid Phase",
            description=None,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        
        with pytest.raises(ValueError):
            services.create_week(
                number=1,
                start_date=date(2025, 1, 7),
                end_date=date(2025, 1, 1),
                focus=None,
                phase_id=phase.id,
            )
