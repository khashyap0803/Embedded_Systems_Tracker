"""Hardware tab for the Embedded Tracker application."""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QComboBox, QLabel, QHBoxLayout, QMessageBox

from ..base import BaseCrudTab, FormField, RippleButton
from ... import services
from ...services import HardwareRecord
from ...models import HardwareCategory, HardwareStatus


class HardwareTab(BaseCrudTab):
    """Tab for managing hardware inventory - boards, sensors, modules, tools."""
    
    entity_name = "Hardware"
    columns = (
        ("ID", "id"),
        ("Name", "name"),
        ("Category", "category"),
        ("Type", "hardware_type"),
        ("MCU/Chip", "mcu"),
        ("Qty", "quantity"),
        ("Status", "status"),
        ("Interface", "interface"),
        ("Project", "project_name"),
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.category_filter = QComboBox()
        self.status_filter = QComboBox()
        super().__init__(parent)
        
        # Add extra buttons after table row buttons
        main_layout = self.layout()
        
        extra_btn_row = QHBoxLayout()
        extra_btn_row.addStretch(1)
        
        self.import_btn = RippleButton("📥 Import JSON")
        self.import_btn.clicked.connect(self._import_from_json)
        extra_btn_row.addWidget(self.import_btn)
        
        self.bom_btn = RippleButton("📋 Compare BOM")
        self.bom_btn.clicked.connect(self._compare_bom)
        extra_btn_row.addWidget(self.bom_btn)
        
        main_layout.addLayout(extra_btn_row)

    def build_filters(self) -> Optional[QHBoxLayout]:
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Category:"))
        self.category_filter.addItem("All", None)
        for cat in HardwareCategory:
            self.category_filter.addItem(cat.value.replace("_", " ").title(), cat)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.category_filter)
        
        layout.addWidget(QLabel("Status:"))
        self.status_filter.addItem("All", None)
        self.status_filter.addItem("✅ Owned Items", "owned")
        self.status_filter.addItem("🛒 To Buy (BOM)", "to_buy")
        self.status_filter.addItem("───────────", None)
        for status in HardwareStatus:
            self.status_filter.addItem(status.value.replace("_", " ").title(), status)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)
        
        layout.addStretch(1)
        return layout

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {
            "category": self.category_filter.currentData(),
        }

    def fetch_records(self, **kwargs: Any) -> List[HardwareRecord]:
        status_val = self.status_filter.currentData()
        
        if status_val == "owned":
            records = services.list_hardware(**kwargs)
            return [r for r in records if r.status in (HardwareStatus.AVAILABLE, HardwareStatus.IN_USE)]
        elif status_val == "to_buy":
            bom_items = services.list_bom_items_to_buy()
            virtual_records = []
            for i, item in enumerate(bom_items):
                category_str = item.get("category", "other").lower().replace(" ", "_")
                try:
                    category = HardwareCategory(category_str)
                except ValueError:
                    category = HardwareCategory.OTHER
                
                virtual_records.append(HardwareRecord(
                    id=-1 * (i + 1),
                    name=f"🛒 {item['name']}",
                    category=category,
                    hardware_type=item.get("priority", "").upper(),
                    mcu="",
                    architecture="",
                    quantity=1,
                    status=HardwareStatus.ORDERED,
                    specifications=item.get("description", ""),
                    features="",
                    interface="",
                    notes=f"₹{item.get('price_inr', 0):,} | Phase {item.get('phase_needed', '?')}, Week {item.get('week_needed', '?')}",
                    purchase_date=None,
                    price_inr=item.get("price_inr", 0),
                    project_id=None,
                    project_name="",
                ))
            return virtual_records
        elif status_val is not None and isinstance(status_val, HardwareStatus):
            kwargs["status"] = status_val
        
        return services.list_hardware(**kwargs)

    def build_form_fields(self, record: Optional[HardwareRecord] = None) -> List[FormField]:
        category_choices = [(cat.value.replace("_", " ").title(), cat) for cat in HardwareCategory]
        status_choices = [(s.value.replace("_", " ").title(), s) for s in HardwareStatus]
        project_choices = [("None", None)] + [
            (p.name, p.id) for p in services.list_projects()
        ]
        return [
            FormField("name", "Name", "text"),
            FormField("category", "Category", "enum", choices=category_choices),
            FormField("hardware_type", "Type", "text", required=False),
            FormField("mcu", "MCU/Chip", "text", required=False),
            FormField("architecture", "Architecture", "text", required=False),
            FormField("quantity", "Quantity", "int"),
            FormField("status", "Status", "enum", choices=status_choices),
            FormField("interface", "Interface", "text", required=False),
            FormField("notes", "Notes", "textarea", required=False),
            FormField("price_inr", "Price (INR)", "float", required=False),
            FormField("project_id", "Project", "enum", choices=project_choices, required=False),
        ]

    def create_record(self, data: Dict[str, Any]) -> Any:
        return services.create_hardware(**data)

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        return services.update_hardware(record_id, **data)

    def delete_record(self, record_id: Any) -> None:
        services.delete_hardware(record_id)

    def _import_from_json(self) -> None:
        """Import hardware items from JSON inventory file."""
        try:
            count = services.seed_hardware_from_json()
            if count > 0:
                QMessageBox.information(
                    self, "Import Complete",
                    f"Successfully imported {count} hardware items from inventory JSON."
                )
                self.refresh()
            else:
                QMessageBox.information(
                    self, "No Items",
                    "No new items to import (all items already exist or JSON is empty)."
                )
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import: {e}")

    def _compare_bom(self) -> None:
        """Compare inventory against BOM and show missing items."""
        try:
            result = services.compare_inventory_vs_bom()
            missing = result.get("missing", [])
            owned = result.get("owned_count", 0)
            total = result.get("bom_total", 0)
            coverage = result.get("coverage_percent", 0)
            
            if not missing:
                QMessageBox.information(
                    self, "BOM Comparison",
                    f"🎉 You have all items from the BOM!\n\n"
                    f"Owned: {owned} items\nBOM Total: {total} items\nCoverage: {coverage}%"
                )
                return
            
            msg = f"BOM Coverage: {coverage}% ({owned}/{total} items)\n\n"
            msg += "Top 10 Missing Items (by priority):\n"
            msg += "-" * 40 + "\n"
            
            for item in missing[:10]:
                priority_emoji = {"essential": "🔴", "recommended": "🟡", "optional": "🟢"}.get(
                    item["priority"], "⚪"
                )
                msg += f"{priority_emoji} {item['name']}\n"
                msg += f"   ₹{item['price_inr']} | Phase {item.get('phase_needed', '?')}, Week {item.get('week_needed', '?')}\n"
            
            if len(missing) > 10:
                msg += f"\n... and {len(missing) - 10} more items"
            
            QMessageBox.information(self, "BOM Comparison", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compare BOM: {e}")
