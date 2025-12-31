"""Metrics tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout

from ..base import BaseCrudTab, FormField
from ... import services
from ...services import MetricRecord


class MetricsTab(BaseCrudTab):
    """Tab for managing metrics and measurements."""
    
    entity_name = "Metric"
    columns = (
        ("#", "__index__"),
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
            FormField("metric_type", "Metric Type", "text"),
            FormField("value", "Value", "float"),
            FormField("unit", "Unit", "text", required=False),
            FormField("recorded_date", "Recorded Date", "date"),
            FormField("phase_id", "Phase", "enum", choices=phase_choices),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_metric(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_metric(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_metric(record_id)
