"""Resources tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import ResourceRecord
from ...models import ResourceType


class ResourcesTab(BaseCrudTab):
    """Tab for managing resources (articles, videos, courses, etc.)."""
    
    entity_name = "Resource"
    columns = (
        ("#", "__index__"),
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
            FormField("title", "Title", "text"),
            FormField("type", "Type", "enum", choices=type_choices),
            FormField("url", "URL", "text", required=False),
            FormField("notes", "Notes", "textarea", required=False),
            FormField("week_id", "Week", "enum", choices=week_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_resource(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_resource(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_resource(record_id)
