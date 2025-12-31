"""Phases tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import PhaseRecord


class PhasesTab(BaseCrudTab):
    """Tab for managing phases in the roadmap."""
    
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
            FormField("name", "Name", "text"),
            FormField("description", "Description", "textarea", required=False),
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
