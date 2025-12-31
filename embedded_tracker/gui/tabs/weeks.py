"""Weeks tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import WeekRecord
from ...models import TaskStatus


class WeeksTab(BaseCrudTab):
    """Tab for managing weeks in the roadmap."""
    
    entity_name = "Week"
    columns = (
        ("#", "__index__"),
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
        
        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_filter.addItem("All", None)
        for status in TaskStatus:
            self.status_filter.addItem(status.value.replace("_", " ").title(), status.value)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)
        
        layout.addStretch(1)
        return layout

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {"phase_id": self.phase_filter.currentData()}

    def fetch_records(self, **kwargs: Any) -> List[WeekRecord]:
        records = services.list_weeks(**kwargs)
        # Client-side status filtering
        status_value = self.status_filter.currentData()
        if status_value is None:
            return records
        return [r for r in records if getattr(r.status, 'value', str(r.status)) == status_value]

    def build_form_fields(self, record: Optional[WeekRecord] = None) -> List[FormField]:
        phase_choices = [(phase.name, phase.id) for phase in services.list_phases()]
        if not phase_choices:
            raise RuntimeError("At least one phase is required before creating weeks.")
        return [
            FormField("number", "Week Number", "int"),
            FormField("start_date", "Start Date", "date"),
            FormField("end_date", "End Date", "date"),
            FormField("focus", "Focus", "text", required=False),
            FormField("phase_id", "Phase", "enum", choices=phase_choices),
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
