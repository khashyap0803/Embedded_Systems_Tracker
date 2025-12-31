# API Reference

## Services Module (`services.py`)

### Phase Operations

```python
def list_phases() -> List[PhaseRecord]
    """Fetch all phases with computed timing statistics."""

def create_phase(
    name: str,
    description: Optional[str],
    start_date: date,
    end_date: date
) -> PhaseRecord
    """Create a new phase. Validates start_date < end_date."""

def update_phase(
    phase_id: int,
    name: object = UNSET,
    description: object = UNSET,
    start_date: object = UNSET,
    end_date: object = UNSET
) -> PhaseRecord
    """Update phase fields. Only provided fields are modified."""

def delete_phase(phase_id: int) -> None
    """Delete phase and all related data (cascading delete)."""
```

### Week Operations

```python
def list_weeks(phase_id: Optional[int] = None) -> List[WeekRecord]
    """List weeks, optionally filtered by phase."""

def create_week(
    number: int,
    start_date: date,
    end_date: date,
    phase_id: int,
    focus: Optional[str] = None
) -> WeekRecord

def update_week(week_id: int, **fields) -> WeekRecord
def delete_week(week_id: int) -> None
```

### Day Operations

```python
def list_days(week_id: Optional[int] = None) -> List[DayRecord]
def create_day(number: int, scheduled_date: date, week_id: int, ...) -> DayRecord
def update_day(day_id: int, **fields) -> DayRecord  
def delete_day(day_id: int) -> None
def override_day_status(day_id: int, status: TaskStatus) -> None
```

### Task Operations

```python
def list_tasks(
    week_id: Optional[int] = None,
    day_id: Optional[int] = None,
    status: Optional[TaskStatus] = None
) -> List[TaskRecord]

def create_task(
    title: str,
    week_id: int,
    description: Optional[str] = None,
    estimated_hours: Optional[float] = None,
    day_id: Optional[int] = None,
    hour_number: Optional[int] = None
) -> TaskRecord

def update_task(task_id: int, **fields) -> TaskRecord
def delete_task(task_id: int) -> None
```

### Timer Operations

```python
def start_task(task_id: int) -> TaskRecord
    """Start working on a task. Sets status to WORKING."""

def pause_task(task_id: int) -> TaskRecord
    """Pause current work. Accumulates work_seconds."""

def take_break(task_id: int) -> TaskRecord
    """Switch to break mode."""

def resume_task(task_id: int) -> TaskRecord
    """Resume from break/pause to working."""

def complete_task(task_id: int) -> TaskRecord
    """Mark task as completed. Records completion timestamp."""

def get_task_timing(task_id: int) -> TimingSnapshot
    """Get current timing state including live calculations."""
```

### Export Operations (`export.py`)

```python
def export_tasks_csv(
    tasks: Sequence[TaskRecord],
    output_path: Optional[Union[str, Path]] = None
) -> str
    """Export tasks to CSV. Returns content, optionally writes file."""

def export_roadmap_csv(
    phases: Sequence[PhaseRecord],
    weeks: Sequence[WeekRecord],
    output_path: Optional[Union[str, Path]] = None
) -> str

def export_tasks_pdf(
    tasks: Sequence[TaskRecord],
    output_path: Union[str, Path],
    title: str = "Tasks Report"
) -> Path
    """Generate PDF report. Requires reportlab."""

def export_roadmap_pdf(
    phases: Sequence[PhaseRecord],
    weeks: Sequence[WeekRecord],
    output_path: Union[str, Path],
    title: str = "Embedded Systems Roadmap"
) -> Path
```

### Utility Functions (`utils.py`)

```python
def utcnow() -> datetime
    """Get current UTC datetime with timezone info."""

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]
    """Convert datetime to UTC, handling naive datetimes."""

def format_local_datetime(
    value: Optional[datetime],
    fmt: str = "%I:%M %p · %d/%m/%Y"
) -> str
    """Format datetime in user's local timezone."""

def format_duration(seconds: float | int | None) -> str
    """Format seconds as HH:MM:SS string."""

def get_user_timezone() -> timezone
    """Detect system timezone with fallbacks."""
```

## Data Classes

### Records (Immutable Data Transfer Objects)

```python
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
class TaskRecord:
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    # ... timing fields ...
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
```

## Enums

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    WORKING = "working"
    BREAK = "break"
    PAUSED = "paused"
    COMPLETED = "completed"

class ProjectStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ON_HOLD = "on_hold"

class ResourceType(str, Enum):
    ARTICLE = "article"
    VIDEO = "video"
    BOOK = "book"
    COURSE = "course"
    # ... more types
```

## Exceptions

```python
class ExportError(Exception):
    """Raised when export operation fails."""
    pass

# Standard exceptions used:
ValueError  # Invalid input, entity not found
sqlite3.Error  # Database operation failed
OSError  # File system error
```
