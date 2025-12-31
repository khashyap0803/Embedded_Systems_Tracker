"""Days tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout, QMenu, QMessageBox

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import DayRecord
from ...models import TaskStatus


class DaysTab(BaseCrudTab):
    """Tab for managing days in the roadmap."""
    
    entity_name = "Day"
    columns = (
        ("#", "__index__"),
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
        self.status_filter = QComboBox()
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
        
        layout.addWidget(QLabel("Status:"))
        self.status_filter.addItem("All", None)
        for status in TaskStatus:
            self.status_filter.addItem(status.value.replace("_", " ").title(), status.value)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)
        
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
        records = services.list_days(**kwargs)
        status_value = self.status_filter.currentData()
        if status_value is None:
            return records
        return [r for r in records if getattr(r.status, 'value', str(r.status)) == status_value]

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
            FormField("focus", "Focus", "text", required=False),
            FormField("notes", "Notes", "textarea", required=False),
            FormField("week_id", "Week", "enum", choices=week_choices),
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
        except Exception as exc:
            QMessageBox.critical(self, "Update Day Status", str(exc))
        else:
            self.refresh()
            self._refresh_hierarchy_tabs()

    def _refresh_hierarchy_tabs(self) -> None:
        window = self.window()
        if window is not None and hasattr(window, "refresh_hierarchy"):
            window.refresh_hierarchy()
