"""Projects tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import ProjectRecord
from ...models import ProjectStatus


class ProjectsTab(BaseCrudTab):
    """Tab for managing projects."""
    
    entity_name = "Project"
    columns = (
        ("#", "__index__"),
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
            FormField("name", "Name", "text"),
            FormField("description", "Description", "textarea", required=False),
            FormField("status", "Status", "enum", choices=status_choices),
            FormField("repo_url", "Repository URL", "text", required=False),
            FormField("demo_url", "Demo URL", "text", required=False),
            FormField("start_date", "Start Date", "date", required=False),
            FormField("due_date", "Due Date", "date", required=False),
            FormField("phase_id", "Phase", "enum", choices=phase_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_project(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_project(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_project(record_id)
