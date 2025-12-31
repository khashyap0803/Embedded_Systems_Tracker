"""Hours tab for the Embedded Tracker application."""

import time
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QComboBox, QLabel, QHBoxLayout, QMenu, QMessageBox, 
    QCheckBox, QTableWidgetItem
)

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import TaskRecord
from ...models import TaskStatus
from ...utils import LIVE_REFRESH_INTERVAL_MS, IDLE_REFRESH_INTERVAL_MS


class HoursTab(BaseCrudTab):
    """Tab for managing hourly tasks in the roadmap."""
    
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
        self.status_filter = QComboBox()
        self.only_open_filter = QCheckBox("Only open items")
        self._last_fetch_time: float = 0.0  # Track when records were fetched (monotonic)
        super().__init__(parent)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self._refresh_timer = QTimer(self)
        self._live_interval_ms = LIVE_REFRESH_INTERVAL_MS
        self._idle_interval_ms = IDLE_REFRESH_INTERVAL_MS
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

        layout.addWidget(QLabel("Status:"))
        self.status_filter.addItem("All", None)
        for status in TaskStatus:
            self.status_filter.addItem(status.value.replace("_", " ").title(), status.value)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)

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
        self._last_fetch_time = time.monotonic()  # Record when we fetched
        records = services.list_tasks(**kwargs)
        status_value = self.status_filter.currentData()
        filtered = []
        for record in records:
            if record.day_id is None or record.hour_number is None:
                continue
            if status_value is not None:
                record_status = getattr(record.status, 'value', str(record.status))
                if record_status != status_value:
                    continue
            filtered.append(record)
        return filtered

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
            FormField("title", "Title", "text"),
            FormField("description", "Description", "textarea", required=False),
            FormField("status", "Status", "enum", choices=status_choices),
            FormField("estimated_hours", "Estimated Hours", "float", required=False),
            FormField("actual_hours", "Actual Hours", "float", required=False),
            FormField("ai_prompt", "AI Prompt", "textarea", required=False),
            FormField("week_id", "Week", "enum", choices=week_choices),
            FormField("day_id", "Day", "enum", choices=day_choices),
            FormField("hour_number", "Hour Number", "int", required=False),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_task(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_task(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_task(record_id)

    def _refresh_if_live(self) -> None:
        """Smart refresh that only updates time columns for live tasks (delta update).
        
        Calculates elapsed time since last fetch to show accurate live timers
        without requiring a full database refresh.
        """
        any_live = any(
            record.is_running or record.is_on_break or record.is_paused for record in self._records
        )
        
        target_interval = self._live_interval_ms if any_live else self._idle_interval_ms
        if self._refresh_timer.interval() != target_interval:
            self._refresh_timer.setInterval(target_interval)
        
        if not any_live:
            return
        
        # Calculate how many seconds have passed since we fetched the data
        elapsed_seconds = int(time.monotonic() - self._last_fetch_time) if self._last_fetch_time else 0
        
        time_col_indices = []
        for col_idx, (_, attr) in enumerate(self.columns):
            if attr in ("work_duration", "break_duration", "pause_duration"):
                time_col_indices.append((col_idx, attr))
        
        for row_idx, record in enumerate(self._records):
            if not (record.is_running or record.is_on_break or record.is_paused):
                continue
            
            for col_idx, attr in time_col_indices:
                # Get base value from record
                if attr == "work_duration":
                    base_seconds = record.work_seconds
                    # Add elapsed time only if this task is running
                    live_seconds = base_seconds + elapsed_seconds if record.is_running else base_seconds
                elif attr == "break_duration":
                    base_seconds = record.break_seconds
                    live_seconds = base_seconds + elapsed_seconds if record.is_on_break else base_seconds
                elif attr == "pause_duration":
                    base_seconds = record.pause_seconds
                    live_seconds = base_seconds + elapsed_seconds if record.is_paused else base_seconds
                else:
                    continue
                
                formatted = self.format_duration(live_seconds)
                
                existing_item = self.table.item(row_idx, col_idx)
                if existing_item is not None:
                    if existing_item.text() != formatted:
                        existing_item.setText(formatted)
                else:
                    item = QTableWidgetItem(formatted)
                    item.setData(Qt.UserRole, self.get_record_id(record))
                    self.table.setItem(row_idx, col_idx, item)

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
        except Exception as exc:
            QMessageBox.critical(self, "Update Status", str(exc))
        else:
            self.refresh()
            self._refresh_hierarchy_tabs()

    def _refresh_hierarchy_tabs(self) -> None:
        window = self.window()
        if window is not None and hasattr(window, "refresh_hierarchy"):
            window.refresh_hierarchy()
