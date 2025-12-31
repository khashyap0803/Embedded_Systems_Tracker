"""Applications tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import ApplicationRecord
from ...models import ApplicationStatus


class ApplicationsTab(BaseCrudTab):
    """Tab for managing job applications."""
    
    entity_name = "Application"
    columns = (
        ("#", "__index__"),
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
            FormField("company", "Company", "text"),
            FormField("role", "Role", "text"),
            FormField("source", "Source", "text", required=False),
            FormField("status", "Status", "enum", choices=status_choices),
            FormField("date_applied", "Date Applied", "date", required=False),
            FormField("next_action", "Next Action", "text", required=False),
            FormField("notes", "Notes", "textarea", required=False),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_application(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_application(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_application(record_id)
