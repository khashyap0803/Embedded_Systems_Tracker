"""Certifications tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import CertificationRecord
from ...models import CertificationStatus


class CertificationsTab(BaseCrudTab):
    """Tab for managing certifications."""
    
    entity_name = "Certification"
    columns = (
        ("#", "__index__"),
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
            FormField("name", "Name", "text"),
            FormField("provider", "Provider", "text", required=False),
            FormField("status", "Status", "enum", choices=status_choices),
            FormField("progress", "Progress (0-1)", "float", placeholder="0.0-1.0"),
            FormField("due_date", "Due Date", "date", required=False),
            FormField("completion_date", "Completion Date", "date", required=False),
            FormField("credential_url", "Credential URL", "text", required=False),
            FormField("phase_id", "Phase", "enum", choices=phase_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_certification(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_certification(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_certification(record_id)
