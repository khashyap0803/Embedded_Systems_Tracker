"""Qt-based GUI for the Embedded Tracker application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from zoneinfo import ZoneInfo

from ..db import ensure_seed_data, init_db
from ..models import ApplicationStatus, CertificationStatus, ProjectStatus, ResourceType, TaskStatus
from .. import services
from ..services import (
    ApplicationRecord,
    CertificationRecord,
    DayRecord,
    MetricRecord,
    PhaseRecord,
    ProjectRecord,
    ResourceRecord,
    TaskRecord,
    WeekRecord,
)
try:
    IST = ZoneInfo("Asia/Kolkata")
except Exception:  # pragma: no cover - fallback when tzdata missing
    IST = timezone(timedelta(hours=5, minutes=30))

DATETIME_DISPLAY_FORMAT = "%I:%M %p · %d/%m/%Y"


def _format_local_datetime(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    local_value = value.astimezone(IST)
    return local_value.strftime(DATETIME_DISPLAY_FORMAT)


@dataclass(slots=True)
class FormField:
    name: str
    label: str
    field_type: str  # line, text, choice, int, float, date
    required: bool = True
    choices: Optional[List[Tuple[str, Any]]] = None
    placeholder: Optional[str] = None


class FormDialog(QDialog):
    """Simple dialog that renders form fields defined by FormField metadata."""

    def __init__(
        self,
        title: str,
        fields: Sequence[FormField],
        initial: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self._fields = list(fields)
        self._widgets: Dict[str, QWidget] = {}
        self._data: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        for field in self._fields:
            widget: QWidget
            if field.field_type == "line":
                widget = QLineEdit()
                if field.placeholder:
                    widget.setPlaceholderText(field.placeholder)
            elif field.field_type == "text":
                widget = QPlainTextEdit()
            elif field.field_type == "choice":
                combo = QComboBox()
                for label, value in field.choices or []:
                    combo.addItem(label, value)
                widget = combo
            elif field.field_type == "int":
                line = QLineEdit()
                line.setValidator(QIntValidator())
                if field.placeholder:
                    line.setPlaceholderText(field.placeholder)
                widget = line
            elif field.field_type == "float":
                line = QLineEdit()
                validator = QDoubleValidator(bottom=-10_000_000, top=10_000_000, decimals=3)
                validator.setNotation(QDoubleValidator.StandardNotation)
                line.setValidator(validator)
                if field.placeholder:
                    line.setPlaceholderText(field.placeholder)
                widget = line
            elif field.field_type == "date":
                line = QLineEdit()
                line.setPlaceholderText(field.placeholder or "YYYY-MM-DD")
                widget = line
            else:
                raise ValueError(f"Unsupported field type: {field.field_type}")

            self._widgets[field.name] = widget
            form_layout.addRow(field.label, widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if initial:
            self._populate_initial(initial)

    def _populate_initial(self, initial: Dict[str, Any]) -> None:
        for name, widget in self._widgets.items():
            value = initial.get(name)
            if isinstance(widget, QLineEdit):
                widget.setText("" if value is None else str(value))
            elif isinstance(widget, QPlainTextEdit):
                widget.setPlainText(value or "")
            elif isinstance(widget, QComboBox):
                for idx in range(widget.count()):
                    if widget.itemData(idx) == value:
                        widget.setCurrentIndex(idx)
                        break

    def _validate_date(self, text: str) -> date:
        if not text:
            raise ValueError("Date required")
        return date.fromisoformat(text)

    def _try_parse_float(self, text: str) -> float:
        if not text:
            raise ValueError("Value required")
        return float(text)

    def _on_accept(self) -> None:
        try:
            data: Dict[str, Any] = {}
            for field in self._fields:
                widget = self._widgets[field.name]
                if isinstance(widget, QLineEdit):
                    text = widget.text().strip()
                    if field.field_type == "int":
                        if not text:
                            if field.required:
                                raise ValueError(f"{field.label} is required")
                            data[field.name] = None
                        else:
                            data[field.name] = int(text)
                    elif field.field_type == "float":
                        if not text:
                            if field.required:
                                raise ValueError(f"{field.label} is required")
                            data[field.name] = None
                        else:
                            data[field.name] = float(text)
                    elif field.field_type == "date":
                        if not text:
                            if field.required:
                                raise ValueError(f"{field.label} is required")
                            data[field.name] = None
                        else:
                            data[field.name] = date.fromisoformat(text)
                    else:
                        if not text and not field.required:
                            data[field.name] = None
                        else:
                            if field.required and not text:
                                raise ValueError(f"{field.label} is required")
                            data[field.name] = text
                elif isinstance(widget, QPlainTextEdit):
                    text_value = widget.toPlainText().strip()
                    if not text_value and not field.required:
                        data[field.name] = None
                    else:
                        data[field.name] = text_value
                elif isinstance(widget, QComboBox):
                    data[field.name] = widget.currentData()
                else:
                    raise ValueError("Unsupported widget")
            self._data = data
            self.accept()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid input", str(exc))

    @property
    def data(self) -> Dict[str, Any]:
        if self._data is None:
            raise RuntimeError("Data accessed before dialog accepted")
        return self._data


class BaseCrudTab(QWidget):
    """Reusable CRUD table with add/edit/delete controls."""

    entity_name: str = "Record"
    columns: Sequence[Tuple[str, str]] = ()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._records: List[Any] = []
        self._suspend_resize = False

        layout = QVBoxLayout(self)
        filters = self.build_filters()
        if filters is not None:
            layout.addLayout(filters)

        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels([label for label, _ in self.columns])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        button_row = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")

        self.refresh_button.clicked.connect(self.refresh)
        self.add_button.clicked.connect(self.handle_add)
        self.edit_button.clicked.connect(self.handle_edit)
        self.delete_button.clicked.connect(self.handle_delete)

        button_row.addWidget(self.refresh_button)
        button_row.addStretch(1)
        button_row.addWidget(self.add_button)
        button_row.addWidget(self.edit_button)
        button_row.addWidget(self.delete_button)
        layout.addLayout(button_row)

        self.refresh()

    # ---- Methods subclasses must implement ---------------------------------

    def fetch_records(self, **kwargs: Any) -> List[Any]:
        raise NotImplementedError

    def build_form_fields(self, record: Optional[Any] = None) -> List[FormField]:
        raise NotImplementedError

    def create_record(self, data: Dict[str, Any]) -> Any:
        raise NotImplementedError

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        raise NotImplementedError

    def delete_record(self, record_id: Any) -> None:
        raise NotImplementedError

    # ---- Hooks for subclasses -----------------------------------------------

    def build_filters(self) -> Optional[QHBoxLayout]:
        return None

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {}

    def build_initial_data(self, record: Any, fields: Sequence[FormField]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for field in fields:
            payload[field.name] = getattr(record, field.name, None)
        return payload

    def get_record_id(self, record: Any) -> Any:
        return getattr(record, "id")

    def get_cell_value(self, record: Any, attr: str) -> Any:
        return getattr(record, attr)

    # ---- Core operations ----------------------------------------------------

    def refresh(self) -> None:
        try:
            records = self.fetch_records(**self.get_filter_kwargs())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, f"Load {self.entity_name}", str(exc))
            return

        self._records = records
        self.table.setRowCount(len(records))
        for row_index, record in enumerate(records):
            for col_index, (_, attr) in enumerate(self.columns):
                if attr == "__index__":
                    value = row_index + 1
                else:
                    value = self.get_cell_value(record, attr)
                item = QTableWidgetItem(self.format_value(value))
                item.setData(Qt.UserRole, self.get_record_id(record))
                self.table.setItem(row_index, col_index, item)
        if not self._suspend_resize:
            self.table.resizeColumnsToContents()
        else:
            self._suspend_resize = False

    def handle_add(self) -> None:
        fields = self.build_form_fields()
        dialog = FormDialog(f"Add {self.entity_name}", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.create_record(dialog.data)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, f"Add {self.entity_name}", str(exc))
            else:
                self.refresh()

    def handle_edit(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        fields = self.build_form_fields(record)
        initial = self.build_initial_data(record, fields)
        dialog = FormDialog(f"Edit {self.entity_name}", fields, initial=initial, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.update_record(self.get_record_id(record), dialog.data)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, f"Edit {self.entity_name}", str(exc))
            else:
                self.refresh()

    def handle_delete(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        confirm = QMessageBox.question(
            self,
            f"Delete {self.entity_name}",
            f"Are you sure you want to delete this {self.entity_name.lower()}?",
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.delete_record(self.get_record_id(record))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, f"Delete {self.entity_name}", str(exc))
        else:
            self.refresh()

    def _selected_record(self) -> Optional[Any]:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._records):
            QMessageBox.information(self, "No selection", "Please select a row first.")
            return None
        return self._records[row]

    @staticmethod
    def format_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, Enum):  # type: ignore[arg-type]
            return value.value  # type: ignore[return-value]
        if isinstance(value, datetime):
            return _format_local_datetime(value)
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    @staticmethod
    def format_duration(value: float | int | None) -> str:
        if value is None:
            total_seconds = 0
        else:
            total_seconds = max(0, int(round(float(value))))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ---- Specific tabs ---------------------------------------------------------


class PhasesTab(BaseCrudTab):
    entity_name = "Phase"
    columns = (
        ("ID", "id"),
        ("Name", "name"),
        ("Status", "status"),
        ("Plan Start", "start_date"),
        ("Plan End", "end_date"),
        ("Actual Start", "actual_start"),
        ("Actual End", "actual_end"),
        ("Work (HH:MM:SS)", "work_seconds"),
        ("Break (HH:MM:SS)", "break_seconds"),
        ("Pause (HH:MM:SS)", "pause_seconds"),
        ("Description", "description"),
    )

    _duration_attrs = {"work_seconds", "break_seconds", "pause_seconds"}

    def fetch_records(self, **_: Any) -> List[PhaseRecord]:
        return services.list_phases()

    def build_form_fields(self, record: Optional[PhaseRecord] = None) -> List[FormField]:
        return [
            FormField("name", "Name", "line"),
            FormField("description", "Description", "text", required=False),
            FormField("start_date", "Start Date", "date"),
            FormField("end_date", "End Date", "date"),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_phase(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_phase(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_phase(record_id)

    def get_cell_value(self, record: PhaseRecord, attr: str) -> Any:
        if attr in self._duration_attrs:
            return self.format_duration(getattr(record, attr))
        return super().get_cell_value(record, attr)


class WeeksTab(BaseCrudTab):
    entity_name = "Week"
    columns = (
        ("ID", "id"),
        ("Phase", "phase_name"),
        ("Week", "number"),
        ("Status", "status"),
        ("Plan Start", "start_date"),
        ("Plan End", "end_date"),
        ("Actual Start", "actual_start"),
        ("Actual End", "actual_end"),
        ("Work (HH:MM:SS)", "work_seconds"),
        ("Break (HH:MM:SS)", "break_seconds"),
        ("Pause (HH:MM:SS)", "pause_seconds"),
        ("Focus", "focus"),
    )

    _duration_attrs = {"work_seconds", "break_seconds", "pause_seconds"}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.phase_filter = QComboBox()
        super().__init__(parent)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Phase:"))
        self.phase_filter.addItem("All", None)
        for phase in services.list_phases():
            self.phase_filter.addItem(phase.name, phase.id)
        self.phase_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.phase_filter)
        layout.addStretch(1)
        return layout

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {"phase_id": self.phase_filter.currentData()}

    def fetch_records(self, **kwargs: Any) -> List[WeekRecord]:
        return services.list_weeks(**kwargs)

    def build_form_fields(self, record: Optional[WeekRecord] = None) -> List[FormField]:
        phase_choices = [(phase.name, phase.id) for phase in services.list_phases()]
        if not phase_choices:
            raise RuntimeError("At least one phase is required before creating weeks.")
        return [
            FormField("number", "Week Number", "int"),
            FormField("start_date", "Start Date", "date"),
            FormField("end_date", "End Date", "date"),
            FormField("focus", "Focus", "line", required=False),
            FormField("phase_id", "Phase", "choice", choices=phase_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_week(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_week(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_week(record_id)

    def get_cell_value(self, record: WeekRecord, attr: str) -> Any:
        if attr in self._duration_attrs:
            return self.format_duration(getattr(record, attr))
        return super().get_cell_value(record, attr)


class DaysTab(BaseCrudTab):
    entity_name = "Day"
    columns = (
        ("ID", "id"),
        ("Phase", "phase_name"),
        ("Week", "week_number"),
        ("Day", "number"),
        ("Date", "scheduled_date"),
        ("Status", "status"),
        ("Work (HH:MM:SS)", "work_seconds"),
        ("Break (HH:MM:SS)", "break_seconds"),
        ("Pause (HH:MM:SS)", "pause_seconds"),
        ("Hours", "hour_count"),
        ("Focus", "focus"),
        ("Notes", "notes"),
    )

    _duration_attrs = {"work_seconds", "break_seconds", "pause_seconds"}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.phase_filter = QComboBox()
        self.week_filter = QComboBox()
        super().__init__(parent)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Phase:"))
        self.phase_filter.addItem("All", None)
        for phase in services.list_phases():
            self.phase_filter.addItem(phase.name, phase.id)
        self.phase_filter.currentIndexChanged.connect(self._on_phase_changed)
        layout.addWidget(self.phase_filter)

        layout.addWidget(QLabel("Week:"))
        self.week_filter.addItem("All", None)
        self.week_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.week_filter)
        layout.addStretch(1)
        self._refresh_week_filter()
        return layout

    def _on_phase_changed(self) -> None:
        self._refresh_week_filter()
        self.refresh()

    def _refresh_week_filter(self) -> None:
        current_week = self.week_filter.currentData()
        self.week_filter.blockSignals(True)
        self.week_filter.clear()
        self.week_filter.addItem("All", None)
        phase_id = self.phase_filter.currentData()
        weeks = services.list_weeks(phase_id=phase_id)
        for week in weeks:
            label = f"Week {week.number} ({week.phase_name})"
            self.week_filter.addItem(label, week.id)
        if current_week is not None:
            for idx in range(self.week_filter.count()):
                if self.week_filter.itemData(idx) == current_week:
                    self.week_filter.setCurrentIndex(idx)
                    break
        self.week_filter.blockSignals(False)

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_filter.currentData(),
            "week_id": self.week_filter.currentData(),
        }

    def fetch_records(self, **kwargs: Any) -> List[DayRecord]:
        return services.list_days(**kwargs)

    def build_form_fields(self, record: Optional[DayRecord] = None) -> List[FormField]:
        weeks = services.list_weeks()
        if not weeks:
            raise RuntimeError("Create at least one week before adding day plans.")
        week_choices = [
            (f"Week {week.number} ({week.phase_name})", week.id) for week in weeks
        ]
        return [
            FormField("number", "Day Number", "int"),
            FormField("scheduled_date", "Scheduled Date", "date"),
            FormField("focus", "Focus", "line", required=False),
            FormField("notes", "Notes", "text", required=False),
            FormField("week_id", "Week", "choice", choices=week_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_day(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_day(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_day(record_id)

    def get_cell_value(self, record: DayRecord, attr: str) -> Any:
        if attr in self._duration_attrs:
            return self.format_duration(getattr(record, attr))
        return super().get_cell_value(record, attr)

    def _show_context_menu(self, position) -> None:
        record = self._selected_record()
        if record is None or record.hour_count:
            return
        menu = QMenu(self)
        status_menu = menu.addMenu("Set Status")
        options = [
            ("Pending", TaskStatus.PENDING),
            ("Working", TaskStatus.WORKING),
            ("Break", TaskStatus.BREAK),
            ("Paused", TaskStatus.PAUSED),
            ("Completed", TaskStatus.COMPLETED),
        ]
        for label, status in options:
            action = status_menu.addAction(label)
            action.triggered.connect(lambda _, s=status, rid=record.id: self._apply_status(rid, s))
        menu.exec(self.table.viewport().mapToGlobal(position))

    def _apply_status(self, record_id: int, status: TaskStatus) -> None:
        try:
            services.override_day_status(record_id, status)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Update Day Status", str(exc))
        else:
            self.refresh()
            self._refresh_hierarchy_tabs()

    def _refresh_hierarchy_tabs(self) -> None:
        window = self.window()
        if window is not None and hasattr(window, "refresh_hierarchy"):
            window.refresh_hierarchy()


class HoursTab(BaseCrudTab):
    entity_name = "Hour"
    columns = (
        ("#", "__index__"),
        ("Phase", "phase_name"),
        ("Week", "week_number"),
        ("Day", "day_number"),
        ("Hour", "hour_number"),
        ("Title", "title"),
        ("Status", "status"),
    ("Work (HH:MM:SS)", "work_duration"),
    ("Break (HH:MM:SS)", "break_duration"),
    ("Pause (HH:MM:SS)", "pause_duration"),
        ("Started", "first_started_at"),
        ("Completed", "completed_at"),
        ("AI Prompt", "ai_prompt"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.phase_filter = QComboBox()
        self.week_filter = QComboBox()
        self.day_filter = QComboBox()
        self.only_open_filter = QCheckBox("Only open items")
        super().__init__(parent)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self._refresh_timer = QTimer(self)
        self._live_interval_ms = 1_000
        self._idle_interval_ms = 15_000
        self._refresh_timer.setInterval(self._idle_interval_ms)
        self._refresh_timer.timeout.connect(self._refresh_if_live)
        self._refresh_timer.start()

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Phase:"))
        self.phase_filter.addItem("All", None)
        for phase in services.list_phases():
            self.phase_filter.addItem(phase.name, phase.id)
        self.phase_filter.currentIndexChanged.connect(self._on_phase_changed)
        layout.addWidget(self.phase_filter)

        layout.addWidget(QLabel("Week:"))
        self.week_filter.addItem("All", None)
        self.week_filter.currentIndexChanged.connect(self._on_week_changed)
        layout.addWidget(self.week_filter)

        layout.addWidget(QLabel("Day:"))
        self.day_filter.addItem("All", None)
        self.day_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.day_filter)

        self.only_open_filter.toggled.connect(self.refresh)
        layout.addWidget(self.only_open_filter)
        layout.addStretch(1)
        self._refresh_week_filter()
        self._refresh_day_filter()
        return layout

    def _on_phase_changed(self) -> None:
        self._refresh_week_filter()
        self.refresh()

    def _on_week_changed(self) -> None:
        self._refresh_day_filter()
        self.refresh()

    def _refresh_week_filter(self) -> None:
        current_week = self.week_filter.currentData()
        self.week_filter.blockSignals(True)
        self.week_filter.clear()
        self.week_filter.addItem("All", None)
        phase_id = self.phase_filter.currentData()
        weeks = services.list_weeks(phase_id=phase_id)
        for week in weeks:
            label = f"Week {week.number} ({week.phase_name})"
            self.week_filter.addItem(label, week.id)
        if current_week is not None:
            for idx in range(self.week_filter.count()):
                if self.week_filter.itemData(idx) == current_week:
                    self.week_filter.setCurrentIndex(idx)
                    break
        self.week_filter.blockSignals(False)
        self._refresh_day_filter()

    def _refresh_day_filter(self) -> None:
        current_day = self.day_filter.currentData()
        self.day_filter.blockSignals(True)
        self.day_filter.clear()
        self.day_filter.addItem("All", None)
        week_id = self.week_filter.currentData()
        phase_id = self.phase_filter.currentData()
        if week_id:
            days = services.list_days(week_id=week_id)
        elif phase_id:
            days = services.list_days(phase_id=phase_id)
        else:
            days = []
        for day in days:
            label = f"Week {day.week_number} · Day {day.number} ({day.scheduled_date})"
            self.day_filter.addItem(label, day.id)
        if current_day is not None:
            for idx in range(self.day_filter.count()):
                if self.day_filter.itemData(idx) == current_day:
                    self.day_filter.setCurrentIndex(idx)
                    break
        self.day_filter.blockSignals(False)

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_filter.currentData(),
            "week_id": self.week_filter.currentData(),
            "day_id": self.day_filter.currentData(),
            "only_open": self.only_open_filter.isChecked(),
        }

    def fetch_records(self, **kwargs: Any) -> List[TaskRecord]:
        records = services.list_tasks(**kwargs)
        return [
            record
            for record in records
            if record.day_id is not None and record.hour_number is not None
        ]

    def get_cell_value(self, record: TaskRecord, attr: str) -> Any:
        if attr == "work_duration":
            return self.format_duration(record.work_seconds)
        if attr == "break_duration":
            return self.format_duration(record.break_seconds)
        if attr == "pause_duration":
            return self.format_duration(record.pause_seconds)
        return super().get_cell_value(record, attr)

    def build_form_fields(self, record: Optional[TaskRecord] = None) -> List[FormField]:
        weeks = services.list_weeks()
        if not weeks:
            raise RuntimeError("Create at least one week before adding hour tasks.")
        week_choices = [
            (f"Week {week.number} ({week.phase_name})", week.id) for week in weeks
        ]
        days = services.list_days()
        day_choices = [
            (f"Week {day.week_number} Day {day.number} ({day.phase_name})", day.id) for day in days
        ]
        if not day_choices:
            raise RuntimeError("Create a day plan before adding hour tasks.")
        status_choices = [
            (status.value.replace("_", " ").title(), status) for status in TaskStatus
        ]
        return [
            FormField("title", "Title", "line"),
            FormField("description", "Description", "text", required=False),
            FormField("status", "Status", "choice", choices=status_choices),
            FormField("estimated_hours", "Estimated Hours", "float", required=False),
            FormField("actual_hours", "Actual Hours", "float", required=False),
            FormField("ai_prompt", "AI Prompt", "text", required=False),
            FormField("week_id", "Week", "choice", choices=week_choices),
            FormField("day_id", "Day", "choice", choices=day_choices),
            FormField("hour_number", "Hour Number", "int", required=False),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_task(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_task(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_task(record_id)

    def _refresh_if_live(self) -> None:
        any_live = any(
            record.is_running or record.is_on_break or record.is_paused for record in self._records
        )
        target_interval = self._live_interval_ms if any_live else self._idle_interval_ms
        if self._refresh_timer.interval() != target_interval:
            self._refresh_timer.setInterval(target_interval)
        if any_live:
            self._suspend_resize = True
            self.refresh()

    def _show_context_menu(self, position) -> None:
        record = self._selected_record()
        if record is None:
            return
        menu = QMenu(self)
        status_menu = menu.addMenu("Update Status")
        status_options = [
            ("Pending", TaskStatus.PENDING),
            ("Working", TaskStatus.WORKING),
            ("Resume", TaskStatus.WORKING),
            ("Break", TaskStatus.BREAK),
            ("Paused", TaskStatus.PAUSED),
            ("Completed", TaskStatus.COMPLETED),
        ]
        for label, status in status_options:
            action = status_menu.addAction(label)
            action.triggered.connect(
                lambda _, s=status, rid=record.id: self._apply_status(rid, s)
            )
        menu.exec(self.table.viewport().mapToGlobal(position))

    def _apply_status(self, record_id: int, status: TaskStatus) -> None:
        try:
            services.update_task_status(record_id, status)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Update Status", str(exc))
        else:
            self.refresh()
            self._refresh_hierarchy_tabs()

    def _refresh_hierarchy_tabs(self) -> None:
        window = self.window()
        if window is not None and hasattr(window, "refresh_hierarchy"):
            window.refresh_hierarchy()


class ResourcesTab(BaseCrudTab):
    entity_name = "Resource"
    columns = (
        ("ID", "id"),
        ("Phase", "phase_name"),
        ("Week", "week_number"),
        ("Title", "title"),
        ("Type", "type"),
        ("URL", "url"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.phase_filter = QComboBox()
        self.week_filter = QComboBox()
        self.type_filter = QComboBox()
        super().__init__(parent)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Phase:"))
        self.phase_filter.addItem("All", None)
        for phase in services.list_phases():
            self.phase_filter.addItem(phase.name, phase.id)
        self.phase_filter.currentIndexChanged.connect(self._on_phase_changed)
        layout.addWidget(self.phase_filter)

        layout.addWidget(QLabel("Week:"))
        self.week_filter.addItem("All", None)
        self.week_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.week_filter)

        layout.addWidget(QLabel("Type:"))
        self.type_filter.addItem("All", None)
        for resource_type in ResourceType:
            label = resource_type.value.title()
            self.type_filter.addItem(label, resource_type)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.type_filter)
        layout.addStretch(1)
        self._refresh_week_filter()
        return layout

    def _on_phase_changed(self) -> None:
        self._refresh_week_filter()
        self.refresh()

    def _refresh_week_filter(self) -> None:
        self.week_filter.blockSignals(True)
        self.week_filter.clear()
        self.week_filter.addItem("All", None)
        weeks = services.list_weeks(phase_id=self.phase_filter.currentData())
        for week in weeks:
            self.week_filter.addItem(f"Week {week.number} ({week.phase_name})", week.id)
        self.week_filter.blockSignals(False)

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_filter.currentData(),
            "week_id": self.week_filter.currentData(),
            "resource_type": self.type_filter.currentData(),
        }

    def fetch_records(self, **kwargs: Any) -> List[ResourceRecord]:
        return services.list_resources(**kwargs)

    def build_form_fields(self, record: Optional[ResourceRecord] = None) -> List[FormField]:
        weeks = services.list_weeks()
        if not weeks:
            raise RuntimeError("Create at least one week before adding resources.")
        week_choices = [
            (f"Week {week.number} ({week.phase_name})", week.id) for week in weeks
        ]
        type_choices = [(member.value.title(), member) for member in ResourceType]
        return [
            FormField("title", "Title", "line"),
            FormField("type", "Type", "choice", choices=type_choices),
            FormField("url", "URL", "line", required=False),
            FormField("notes", "Notes", "text", required=False),
            FormField("week_id", "Week", "choice", choices=week_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_resource(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_resource(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_resource(record_id)


class ProjectsTab(BaseCrudTab):
    entity_name = "Project"
    columns = (
        ("ID", "id"),
        ("Name", "name"),
        ("Phase", "phase_name"),
        ("Status", "status"),
        ("Due", "due_date"),
        ("Repository", "repo_url"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.phase_filter = QComboBox()
        self.status_filter = QComboBox()
        super().__init__(parent)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Phase:"))
        self.phase_filter.addItem("All", None)
        for phase in services.list_phases():
            self.phase_filter.addItem(phase.name, phase.id)
        self.phase_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.phase_filter)

        layout.addWidget(QLabel("Status:"))
        self.status_filter.addItem("All", None)
        for status in ProjectStatus:
            self.status_filter.addItem(status.value.title().replace("_", " "), status)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)
        layout.addStretch(1)
        return layout

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {"phase_id": self.phase_filter.currentData(), "status": self.status_filter.currentData()}

    def fetch_records(self, **kwargs: Any) -> List[ProjectRecord]:
        return services.list_projects(**kwargs)

    def build_form_fields(self, record: Optional[ProjectRecord] = None) -> List[FormField]:
        phase_choices = [("Unassigned", None)] + [
            (phase.name, phase.id) for phase in services.list_phases()
        ]
        status_choices = [
            (status.value.title().replace("_", " "), status) for status in ProjectStatus
        ]
        return [
            FormField("name", "Name", "line"),
            FormField("description", "Description", "text", required=False),
            FormField("status", "Status", "choice", choices=status_choices),
            FormField("repo_url", "Repository URL", "line", required=False),
            FormField("demo_url", "Demo URL", "line", required=False),
            FormField("start_date", "Start Date", "date", required=False),
            FormField("due_date", "Due Date", "date", required=False),
            FormField("phase_id", "Phase", "choice", choices=phase_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_project(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_project(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_project(record_id)


class CertificationsTab(BaseCrudTab):
    entity_name = "Certification"
    columns = (
        ("ID", "id"),
        ("Name", "name"),
        ("Phase", "phase_name"),
        ("Status", "status"),
        ("Progress", "progress"),
        ("Due", "due_date"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.status_filter = QComboBox()
        super().__init__(parent)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Status:"))
        self.status_filter.addItem("All", None)
        for status in CertificationStatus:
            self.status_filter.addItem(status.value.title().replace("_", " "), status)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)
        layout.addStretch(1)
        return layout

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {"status": self.status_filter.currentData()}

    def fetch_records(self, **kwargs: Any) -> List[CertificationRecord]:
        return services.list_certifications(**kwargs)

    def build_form_fields(self, record: Optional[CertificationRecord] = None) -> List[FormField]:
        phase_choices = [("Unassigned", None)] + [
            (phase.name, phase.id) for phase in services.list_phases()
        ]
        status_choices = [
            (status.value.title().replace("_", " "), status) for status in CertificationStatus
        ]
        return [
            FormField("name", "Name", "line"),
            FormField("provider", "Provider", "line", required=False),
            FormField("status", "Status", "choice", choices=status_choices),
            FormField("progress", "Progress (0-1)", "float", placeholder="0.0-1.0"),
            FormField("due_date", "Due Date", "date", required=False),
            FormField("completion_date", "Completion Date", "date", required=False),
            FormField("credential_url", "Credential URL", "line", required=False),
            FormField("phase_id", "Phase", "choice", choices=phase_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_certification(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_certification(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_certification(record_id)


class ApplicationsTab(BaseCrudTab):
    entity_name = "Application"
    columns = (
        ("ID", "id"),
        ("Company", "company"),
        ("Role", "role"),
        ("Status", "status"),
        ("Applied", "date_applied"),
        ("Next Action", "next_action"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.status_filter = QComboBox()
        super().__init__(parent)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Status:"))
        self.status_filter.addItem("All", None)
        for status in ApplicationStatus:
            self.status_filter.addItem(status.value.title().replace("_", " "), status)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)
        layout.addStretch(1)
        return layout

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {"status": self.status_filter.currentData()}

    def fetch_records(self, **kwargs: Any) -> List[ApplicationRecord]:
        return services.list_applications(**kwargs)

    def build_form_fields(self, record: Optional[ApplicationRecord] = None) -> List[FormField]:
        status_choices = [
            (status.value.title().replace("_", " "), status) for status in ApplicationStatus
        ]
        return [
            FormField("company", "Company", "line"),
            FormField("role", "Role", "line"),
            FormField("source", "Source", "line", required=False),
            FormField("status", "Status", "choice", choices=status_choices),
            FormField("date_applied", "Date Applied", "date", required=False),
            FormField("next_action", "Next Action", "line", required=False),
            FormField("notes", "Notes", "text", required=False),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_application(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_application(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_application(record_id)


class MetricsTab(BaseCrudTab):
    entity_name = "Metric"
    columns = (
        ("ID", "id"),
        ("Date", "recorded_date"),
        ("Type", "metric_type"),
        ("Value", "value"),
        ("Unit", "unit"),
        ("Phase", "phase_name"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.phase_filter = QComboBox()
        super().__init__(parent)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Phase:"))
        self.phase_filter.addItem("All", None)
        for phase in services.list_phases():
            self.phase_filter.addItem(phase.name, phase.id)
        self.phase_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.phase_filter)
        layout.addStretch(1)
        return layout

    def get_filter_kwargs(self) -> Dict[str, Any]:
        phase_id = self.phase_filter.currentData()
        return {"phase_id": phase_id}

    def fetch_records(self, **kwargs: Any) -> List[MetricRecord]:
        return services.list_metrics(**kwargs)

    def build_form_fields(self, record: Optional[MetricRecord] = None) -> List[FormField]:
        phase_choices = [("Unassigned", None)] + [
            (phase.name, phase.id) for phase in services.list_phases()
        ]
        return [
            FormField("metric_type", "Metric Type", "line"),
            FormField("value", "Value", "float"),
            FormField("unit", "Unit", "line", required=False),
            FormField("recorded_date", "Recorded Date", "date"),
            FormField("phase_id", "Phase", "choice", choices=phase_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_metric(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_metric(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_metric(record_id)


class MainWindow(QMainWindow):
    """Primary application window hosting all management tabs."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Embedded Tracker")
        self.resize(1280, 800)

        self.tabs = QTabWidget()

        self.phases_tab = PhasesTab(self)
        self.weeks_tab = WeeksTab(self)
        self.days_tab = DaysTab(self)
        self.hours_tab = HoursTab(self)
        self.resources_tab = ResourcesTab(self)
        self.projects_tab = ProjectsTab(self)
        self.certifications_tab = CertificationsTab(self)
        self.applications_tab = ApplicationsTab(self)
        self.metrics_tab = MetricsTab(self)

        self.tabs.addTab(self.phases_tab, "Phases")
        self.tabs.addTab(self.weeks_tab, "Weeks")
        self.tabs.addTab(self.days_tab, "Days")
        self.tabs.addTab(self.hours_tab, "Hours")
        self.tabs.addTab(self.resources_tab, "Resources")
        self.tabs.addTab(self.projects_tab, "Projects")
        self.tabs.addTab(self.certifications_tab, "Certifications")
        self.tabs.addTab(self.applications_tab, "Applications")
        self.tabs.addTab(self.metrics_tab, "Metrics")

        self.setCentralWidget(self.tabs)

    def refresh_hierarchy(self) -> None:
        self.phases_tab.refresh()
        self.weeks_tab.refresh()
        self.days_tab.refresh()


def run() -> None:
    """Initialise the database and start the Qt event loop."""

    init_db()
    ensure_seed_data()
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
