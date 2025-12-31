"""Shared GUI components for the Embedded Tracker application.

This module contains base classes and widgets used by all tabs:
- StatusDelegate: Custom delegate for status pill rendering
- RippleButton: Animated button with ripple effect
- FormField/FormDialog: Form generation utilities
- BaseCrudTab: Base class for CRUD tabs
- Theme strings (DARK_THEME, LIGHT_THEME)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import Qt, QTimer, QSettings, QPropertyAnimation, QEasingCurve, QPoint, QEvent, Property, QRectF, QObject, QDate
from PySide6.QtGui import QDoubleValidator, QIntValidator, QAction, QKeySequence, QColor, QPainter, QBrush, QPen, QPainterPath, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolTip,
)

from ..models import TaskStatus
from .. import services
from .workers import run_in_background, LoadingState


# -----------------------------------------------------------------------------
# Undo/Redo Support (Command Pattern)
# -----------------------------------------------------------------------------

from abc import ABC, abstractmethod
from collections import deque


class UndoCommand(ABC):
    """Abstract base class for undoable commands."""
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the command."""
        pass


class DeleteCommand(UndoCommand):
    """Command for deleting a record (can be undone by re-creating)."""
    
    def __init__(self, tab: 'BaseCrudTab', record_id: int, record_data: dict):
        self.tab = tab
        self.record_id = record_id
        self.record_data = record_data  # Snapshot of record before deletion
        self._deleted_id = None
    
    def execute(self) -> None:
        self.tab.delete_record(self.record_id)
    
    def undo(self) -> None:
        # Re-create the record
        self._deleted_id = self.tab.create_record(self.record_data)
        self.tab.refresh()
    
    @property
    def description(self) -> str:
        title = self.record_data.get('title', self.record_data.get('name', f'ID {self.record_id}'))
        return f"Delete {self.tab.entity_name}: {title}"


class UndoStack:
    """Manages undo/redo history for a tab."""
    
    MAX_HISTORY = 20
    
    def __init__(self):
        self._undo_stack: deque[UndoCommand] = deque(maxlen=self.MAX_HISTORY)
        self._redo_stack: deque[UndoCommand] = deque(maxlen=self.MAX_HISTORY)
    
    def push(self, command: UndoCommand) -> None:
        """Add a command to the undo stack (clears redo stack)."""
        self._undo_stack.append(command)
        self._redo_stack.clear()
    
    def undo(self) -> bool:
        """Undo the last command. Returns True if successful."""
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return True
    
    def redo(self) -> bool:
        """Redo the last undone command. Returns True if successful."""
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        return True
    
    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)
    
    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)
    
    @property
    def undo_description(self) -> str:
        if self._undo_stack:
            return self._undo_stack[-1].description
        return ""
    
    @property
    def redo_description(self) -> str:
        if self._redo_stack:
            return self._redo_stack[-1].description
        return ""


# Status colors for pill rendering
STATUS_COLORS = {
    "pending": QColor("#bdc3c7"),
    "working": QColor("#e67e22"),
    "break": QColor("#f1c40f"),
    "paused": QColor("#95a5a6"),
    "completed": QColor("#27ae60"),
    "planned": QColor("#9b59b6"),
    "in_progress": QColor("#e67e22"),
    "done": QColor("#27ae60"),
    "rejected": QColor("#c0392b"),
}


class StatusDelegate(QStyledItemDelegate):
    """Custom delegate to render status values as colored pills with centered text."""
    
    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: Any
    ) -> None:
        text = str(index.data() or "")
        status_key = text.lower().replace(" ", "_")
        color = STATUS_COLORS.get(status_key, QColor("#7f8c8d"))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Calculate pill rect
        rect = option.rect.adjusted(4, 6, -4, -6)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 12, 12)

        # Fill pill background
        painter.fillPath(path, QBrush(color))

        # Draw text centered
        painter.setPen(QPen(Qt.white))
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, text.title())

        # Draw selection border if selected
        from PySide6.QtWidgets import QStyle
        if option.state & QStyle.State_Selected:
            pen = QPen(QColor("#ffffff"), 2)
            painter.setPen(pen)
            painter.drawPath(path)

        painter.restore()

    def helpEvent(self, event: QEvent, view: Any, option: QStyleOptionViewItem, index: Any) -> bool:
        if event.type() == QEvent.ToolTip:
            QToolTip.showText(event.globalPos(), str(index.data() or ""))
            return True
        return super().helpEvent(event, view, option, index)


class RippleButton(QPushButton):
    """Animated button with ripple effect on click."""
    
    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self._radius = 0.0
        self._pos = QPoint(0, 0)
        self._anim = QPropertyAnimation(self, b"radius_prop", self)
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutQuad)

    @Property(float)
    def radius_prop(self) -> float:
        return self._radius

    @radius_prop.setter
    def radius_prop(self, r: float) -> None:
        self._radius = r
        self.update()

    def mousePressEvent(self, event: QEvent) -> None:
        self._pos = event.pos()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(max(self.width(), self.height()) * 1.5)
        self._anim.start()
        super().mousePressEvent(event)

    def paintEvent(self, event: QEvent) -> None:
        super().paintEvent(event)
        if self._radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(255, 255, 255, 50))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self._pos, int(self._radius), int(self._radius))


@dataclass(slots=True)
class FormField:
    """Metadata for a single form field."""
    name: str
    label: str
    field_type: str  # "text", "int", "float", "date", "textarea", "enum"
    required: bool = True
    choices: Optional[List[Tuple[str, Any]]] = None
    placeholder: Optional[str] = None


class FormDialog(QDialog):
    """Simple dialog that renders form fields defined by FormField metadata."""

    def __init__(
        self,
        title: str,
        fields: Sequence[FormField],
        initial: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(450)
        self._fields = fields
        self._widgets: Dict[str, QWidget] = {}
        self._data: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        for field in fields:
            if field.field_type == "textarea":
                widget = QPlainTextEdit()
                widget.setMaximumHeight(100)
            elif field.field_type == "enum" and field.choices:
                widget = QComboBox()
                for label, value in field.choices:
                    widget.addItem(label, value)
            elif field.field_type == "int":
                line = QLineEdit()
                validator = QIntValidator()
                line.setValidator(validator)
                if field.placeholder:
                    line.setPlaceholderText(field.placeholder)
                widget = line
            elif field.field_type == "float":
                line = QLineEdit()
                validator = QDoubleValidator()
                validator.setDecimals(2)
                line.setValidator(validator)
                if field.placeholder:
                    line.setPlaceholderText(field.placeholder)
                widget = line
            elif field.field_type == "date":
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                date_edit.setDisplayFormat("yyyy-MM-dd")
                date_edit.setDate(QDate.currentDate())
                date_edit.setSpecialValueText(" ")
                if not field.required:
                    date_edit.setMinimumDate(QDate(1900, 1, 1))
                widget = date_edit
            else:
                line = QLineEdit()
                if field.placeholder:
                    line.setPlaceholderText(field.placeholder)
                widget = line

            self._widgets[field.name] = widget
            form_layout.addRow(field.label, widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if initial:
            self._populate_initial(initial)

    def _populate_initial(self, initial: Dict[str, Any]) -> None:
        for name, widget in self._widgets.items():
            value = initial.get(name)
            if isinstance(widget, QLineEdit):
                widget.setText("" if value is None else str(value))
            elif isinstance(widget, QPlainTextEdit):
                widget.setPlainText(value or "")
            elif isinstance(widget, QComboBox):
                for idx in range(widget.count()):
                    if widget.itemData(idx) == value:
                        widget.setCurrentIndex(idx)
                        break
            elif isinstance(widget, QDateEdit):
                if value is not None and isinstance(value, date):
                    widget.setDate(QDate(value.year, value.month, value.day))
                elif value is None:
                    widget.setDate(widget.minimumDate())

    def _on_accept(self) -> None:
        # Clear previous error styling
        for widget in self._widgets.values():
            widget.setStyleSheet("")
        
        errors: list[tuple[str, QWidget, str]] = []  # (field_name, widget, message)
        data: Dict[str, Any] = {}
        
        for field in self._fields:
            widget = self._widgets[field.name]
            try:
                if isinstance(widget, QLineEdit):
                    text = widget.text().strip()
                    if field.field_type == "int":
                        if not text:
                            if field.required:
                                errors.append((field.name, widget, f"{field.label} is required"))
                                continue
                            data[field.name] = None
                        else:
                            data[field.name] = int(text)
                    elif field.field_type == "float":
                        if not text:
                            if field.required:
                                errors.append((field.name, widget, f"{field.label} is required"))
                                continue
                            data[field.name] = None
                        else:
                            data[field.name] = float(text)
                    else:
                        if not text and field.required:
                            errors.append((field.name, widget, f"{field.label} is required"))
                            continue
                        data[field.name] = text if text else None
                elif isinstance(widget, QPlainTextEdit):
                    text_value = widget.toPlainText().strip()
                    if not text_value and field.required:
                        errors.append((field.name, widget, f"{field.label} is required"))
                        continue
                    data[field.name] = text_value if text_value else None
                elif isinstance(widget, QComboBox):
                    data[field.name] = widget.currentData()
                elif isinstance(widget, QDateEdit):
                    qdate = widget.date()
                    if qdate == widget.minimumDate():
                        if field.required:
                            errors.append((field.name, widget, f"{field.label} is required"))
                            continue
                        data[field.name] = None
                    else:
                        data[field.name] = date(qdate.year(), qdate.month(), qdate.day())
            except ValueError as e:
                errors.append((field.name, widget, str(e)))
        
        if errors:
            # Highlight invalid fields with red border
            for field_name, widget, msg in errors:
                widget.setStyleSheet("border: 2px solid #e74c3c; border-radius: 4px;")
            
            # Show consolidated error message
            error_messages = "\n".join([f"• {msg}" for _, _, msg in errors])
            QMessageBox.warning(self, "Validation Error", f"Please fix the following:\n\n{error_messages}")
            return
        
        self._data = data
        self.accept()

    @property
    def data(self) -> Dict[str, Any]:
        if self._data is None:
            raise RuntimeError("Data accessed before dialog accepted")
        return self._data


class BaseCrudTab(QWidget):
    """Reusable CRUD table with add/edit/delete controls."""

    entity_name: str = "Record"
    columns: Sequence[Tuple[str, str]] = ()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._records: List[Any] = []
        self._filtered_records: List[Any] = []  # Records after search filter
        self._suspend_resize = False
        self._loading = LoadingState()
        self._active_workers: List[Any] = []  # Keep references to prevent GC
        self._undo_stack = UndoStack()  # Undo/Redo support

        layout = QVBoxLayout(self)
        filters = self.build_filters()
        if filters is not None:
            layout.addLayout(filters)

        # Search box for filtering
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to filter rows...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self._apply_search_filter)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels([label for label, _ in self.columns])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setVisible(False)
        self.table.viewport().installEventFilter(self)
        layout.addWidget(self.table)

        # Apply pill renderers for status columns
        for i, (_, field_name) in enumerate(self.columns):
            if "status" in field_name.lower():
                self.table.setItemDelegateForColumn(i, StatusDelegate(self.table))

        button_row = QHBoxLayout()
        self.refresh_button = RippleButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        button_row.addWidget(self.refresh_button)

        self.add_button = RippleButton("Add")
        self.add_button.clicked.connect(self.handle_add)
        button_row.addWidget(self.add_button)

        self.edit_button = RippleButton("Edit")
        self.edit_button.clicked.connect(self.handle_edit)
        button_row.addWidget(self.edit_button)

        self.delete_button = RippleButton("Delete")
        self.delete_button.clicked.connect(self.handle_delete)
        button_row.addWidget(self.delete_button)

        # Undo/Redo buttons
        self.undo_button = RippleButton("↶ Undo")
        self.undo_button.clicked.connect(self.handle_undo)
        self.undo_button.setEnabled(False)
        button_row.addWidget(self.undo_button)

        self.redo_button = RippleButton("↷ Redo")
        self.redo_button.clicked.connect(self.handle_redo)
        self.redo_button.setEnabled(False)
        button_row.addWidget(self.redo_button)

        button_row.addStretch(1)
        layout.addLayout(button_row)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Handle Shift+Scroll for horizontal scrolling."""
        if obj == self.table.viewport() and event.type() == QEvent.Wheel:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ShiftModifier:
                h_bar = self.table.horizontalScrollBar()
                delta = event.angleDelta().y()
                h_bar.setValue(h_bar.value() - delta)
                return True
        return super().eventFilter(obj, event)

    # ---- Abstract methods (override in subclasses) ---------------------------
    def fetch_records(self, **kwargs: Any) -> List[Any]:
        raise NotImplementedError

    def build_form_fields(self, record: Optional[Any] = None) -> Sequence[FormField]:
        raise NotImplementedError

    def create_record(self, data: Dict[str, Any]) -> Any:
        raise NotImplementedError

    def update_record(self, record_id: Any, data: Dict[str, Any]) -> Any:
        raise NotImplementedError

    def delete_record(self, record_id: Any) -> None:
        raise NotImplementedError

    def build_filters(self) -> Optional[QHBoxLayout]:
        return None

    def get_filter_kwargs(self) -> Dict[str, Any]:
        return {}

    def build_initial_data(self, record: Any, fields: Sequence[FormField]) -> Dict[str, Any]:
        return {f.name: getattr(record, f.name, None) for f in fields}

    def get_record_id(self, record: Any) -> Any:
        return record.id

    def get_cell_value(self, record: Any, attr: str) -> Any:
        return getattr(record, attr)

    # ---- Core operations ----------------------------------------------------

    def refresh(self) -> None:
        """Refresh the table with data from the database.
        
        Using synchronous refresh for stability. Background threading
        was causing memory issues with signal connections.
        """
        filter_kwargs = self.get_filter_kwargs()
        
        try:
            records = self.fetch_records(**filter_kwargs)
            self._records = records
            self._apply_search_filter()  # Apply any active search filter
        except Exception as exc:
            QMessageBox.critical(self, f"Load {self.entity_name}", str(exc))

    def _apply_search_filter(self) -> None:
        """Filter records based on search box text and repopulate table."""
        search_text = self.search_box.text().strip().lower()
        
        if not search_text:
            # No search filter, show all records
            self._filtered_records = self._records
        else:
            # Filter records where any column value contains the search text
            self._filtered_records = []
            for record in self._records:
                for _, attr in self.columns:
                    if attr == "__index__":
                        continue
                    value = str(self.get_cell_value(record, attr)).lower()
                    if search_text in value:
                        self._filtered_records.append(record)
                        break  # Found match, move to next record
        
        self._populate_table(self._filtered_records)

    def _populate_table(self, records: List[Any]) -> None:
        """Populate the table with records (called on UI thread)."""
        self.table.setRowCount(len(records))
        for row_index, record in enumerate(records):
            status_val = str(getattr(record, "status", "")).lower()
            row_bg = None
            if "working" in status_val:
                row_bg = QColor(230, 126, 34, 50)
            elif "break" in status_val:
                row_bg = QColor(241, 196, 15, 50)
            elif "paused" in status_val:
                row_bg = QColor(127, 140, 141, 50)
            elif "completed" in status_val:
                row_bg = QColor(39, 174, 96, 40)

            for col_index, (_, attr) in enumerate(self.columns):
                if attr == "__index__":
                    value = row_index + 1
                else:
                    value = self.get_cell_value(record, attr)

                item = QTableWidgetItem(self.format_value(value))
                if row_bg:
                    item.setBackground(row_bg)

                item.setData(Qt.UserRole, self.get_record_id(record))
                self.table.setItem(row_index, col_index, item)

        if not self._suspend_resize:
            self.table.resizeColumnsToContents()
        else:
            self._suspend_resize = False

    def handle_add(self) -> None:
        """Add a new record."""
        try:
            fields = self.build_form_fields()
        except RuntimeError as e:
            QMessageBox.warning(self, f"Add {self.entity_name}", str(e))
            return
            
        dialog = FormDialog(f"Add {self.entity_name}", fields, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.create_record(dialog.data)
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, f"Add {self.entity_name}", str(exc))

    def handle_edit(self) -> None:
        """Edit the selected record."""
        record = self._selected_record()
        if record is None:
            return
        fields = self.build_form_fields(record)
        initial = self.build_initial_data(record, fields)
        dialog = FormDialog(f"Edit {self.entity_name}", fields, initial=initial, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                record_id = self.get_record_id(record)
                self.update_record(record_id, dialog.data)
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, f"Edit {self.entity_name}", str(exc))

    def handle_delete(self) -> None:
        """Delete the selected record (with undo support)."""
        record = self._selected_record()
        if record is None:
            return
        confirm = QMessageBox.question(
            self,
            f"Delete {self.entity_name}",
            f"Are you sure you want to delete this {self.entity_name.lower()}?",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            record_id = self.get_record_id(record)
            # Snapshot record data for undo
            fields = self.build_form_fields(record)
            record_data = self.build_initial_data(record, fields)
            
            # Create and execute command
            command = DeleteCommand(self, record_id, record_data)
            command.execute()
            self._undo_stack.push(command)
            self._update_undo_ui()
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, f"Delete {self.entity_name}", str(exc))
    
    def handle_undo(self) -> None:
        """Undo the last action."""
        if self._undo_stack.undo():
            self._update_undo_ui()
            self.refresh()
    
    def handle_redo(self) -> None:
        """Redo the last undone action."""
        if self._undo_stack.redo():
            self._update_undo_ui()
            self.refresh()
    
    def _update_undo_ui(self) -> None:
        """Update the enabled state and tooltips of undo/redo buttons."""
        self.undo_button.setEnabled(self._undo_stack.can_undo)
        self.redo_button.setEnabled(self._undo_stack.can_redo)
        
        if self._undo_stack.can_undo:
            self.undo_button.setToolTip(f"Undo: {self._undo_stack.undo_description}")
        else:
            self.undo_button.setToolTip("Nothing to undo")
        
        if self._undo_stack.can_redo:
            self.redo_button.setToolTip(f"Redo: {self._undo_stack.redo_description}")
        else:
            self.redo_button.setToolTip("Nothing to redo")

    def _selected_record(self) -> Optional[Any]:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._records):
            QMessageBox.information(self, "No selection", "Please select a row first.")
            return None
        return self._records[row]

    @staticmethod
    def format_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, Enum):
            return value.value.replace("_", " ").title()
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    @staticmethod
    def format_duration(value: float | int | None) -> str:
        if value is None or value == 0:
            return "0:00:00"
        total_seconds = int(value)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"


# ═══════════════════════════════════════════════════════════════════════════════
# EMBER THEME - Dark & Warm Orange
# ═══════════════════════════════════════════════════════════════════════════════
DARK_THEME = """
/* ─── Global Styles ─── */
* {
    border-radius: 16px;
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
}
QWidget {
    background-color: #121212;
    color: #ecf0f1;
    font-size: 14px;
    selection-background-color: #d35400;
    selection-color: #ffffff;
}
QMainWindow {
    background-color: #121212;
}
QDialog {
    background-color: #1e1e1e;
    border: 1px solid #333;
}

/* ─── Tab Widget ─── */
QTabWidget::pane {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 20px;
    padding: 15px;
    margin-top: 15px;
}
QTabBar::tab {
    background-color: #121212;
    color: #95a5a6;
    padding: 12px 30px;
    margin-right: 10px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 13px;
    text-transform: uppercase;
}
QTabBar::tab:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e67e22, stop:1 #d35400);
    color: #ffffff;
    border: none;
}
QTabBar::tab:hover:!selected {
    background-color: #2c3e50;
    color: #ecf0f1;
}

/* ─── Table Widget ─── */
QTableWidget {
    background-color: #1e1e1e;
    alternate-background-color: #252525;
    gridline-color: transparent;
    border: none;
    padding: 10px;
}
/* ─── Scrollbars (Orange) ─── */
QScrollBar:vertical {
    background-color: transparent;
    width: 14px;
    margin: 4px;
}
QScrollBar::handle:vertical {
    background-color: #e67e22;
    min-height: 20px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover { background-color: #d35400; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 14px;
    margin: 4px;
}
QScrollBar::handle:horizontal {
    background-color: #e67e22;
    min-width: 20px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal:hover { background-color: #d35400; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QTableWidget::item {
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 4px;
}
QTableWidget::item:selected {
    background-color: rgba(230, 126, 34, 0.3);
    color: #ffffff;
    border: 1px solid #e67e22;
    font-weight: bold;
}
QHeaderView::section {
    background-color: #1e1e1e;
    color: #e67e22;
    padding: 15px;
    border: none;
    font-weight: 800;
    text-transform: uppercase;
    font-size: 12px;
    letter-spacing: 1.2px;
}

/* ─── Buttons ─── */
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e67e22, stop:1 #d35400);
    color: #ffffff;
    border: none;
    padding: 14px 28px;
    border-radius: 14px;
    font-weight: bold;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f39c12, stop:1 #e67e22);
    margin-top: -2px;
}
QPushButton:pressed {
    background-color: #a04000;
    margin-top: 2px;
}
QPushButton:disabled {
    background-color: #2c3e50;
    color: #7f8c8d;
}

/* ─── Input Fields ─── */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2c2c2c;
    color: #ffffff;
    border: 2px solid #333;
    padding: 14px;
    border-radius: 12px;
    selection-background-color: #e67e22;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 2px solid #e67e22;
    background-color: #333;
}
QComboBox::drop-down {
    border: none;
    width: 25px;
}
QComboBox QAbstractItemView {
    border: 2px solid #333;
    border-radius: 12px;
    background-color: #2c2c2c;
    selection-background-color: #e67e22;
    selection-color: #ffffff;
    padding: 5px;
    outline: none;
}

/* ─── Menu Bar ─── */
QMenuBar {
    background-color: #121212;
    padding: 10px;
}
QMenuBar::item {
    padding: 10px 20px;
    border-radius: 8px;
    color: #ecf0f1;
}
QMenuBar::item:selected {
    background-color: #e67e22;
    color: #ffffff;
}
QMenu {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 8px;
}
QMenu::item {
    padding: 12px 24px;
    border-radius: 8px;
}
QMenu::item:selected {
    background-color: #e67e22;
    color: #ffffff;
}

/* ─── Misc ─── */
QProgressBar {
    background-color: #333;
    border-radius: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e67e22, stop:1 #f1c40f);
    border-radius: 10px;
}
QMessageBox { background-color: #1e1e1e; }
"""

# ═══════════════════════════════════════════════════════════════════════════════
# DAWN THEME - Light & Warm Coral
# ═══════════════════════════════════════════════════════════════════════════════
LIGHT_THEME = """
/* ─── Global Styles ─── */
* {
    border-radius: 16px;
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
}
QWidget {
    background-color: #fffbf0;
    color: #2d3436;
    font-size: 14px;
    selection-background-color: #ff7f50;
    selection-color: #ffffff;
}
QMainWindow {
    background-color: #fffbf0;
}
QDialog {
    background-color: #ffffff;
    border: 1px solid #ffeaa7;
}

/* ─── Tab Widget ─── */
QTabWidget::pane {
    background-color: #ffffff;
    border: 1px solid #ffeaa7;
    border-radius: 20px;
    padding: 15px;
    margin-top: 15px;
}
QTabBar::tab {
    background-color: #fffbf0;
    color: #636e72;
    padding: 12px 30px;
    margin-right: 10px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 13px;
    text-transform: uppercase;
}
QTabBar::tab:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff7f50, stop:1 #ff6b6b);
    color: #ffffff;
    border: none;
}
QTabBar::tab:hover:!selected {
    background-color: #ffeaa7;
    color: #d35400;
}

/* ─── Table Widget ─── */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #fff9e6;
    gridline-color: transparent;
    border: none;
    padding: 10px;
}
QTableWidget::item {
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 4px;
}
QTableWidget::item:selected {
    background-color: rgba(255, 127, 80, 0.3);
    color: #2d3436;
    border: 1px solid #ff7f50;
    font-weight: bold;
}
QHeaderView::section {
    background-color: #ffffff;
    color: #ff7f50;
    padding: 15px;
    border: none;
    font-weight: 800;
    text-transform: uppercase;
    font-size: 12px;
    letter-spacing: 1.2px;
}

/* ─── Buttons ─── */
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff7f50, stop:1 #ff6b6b);
    color: #ffffff;
    border: none;
    padding: 14px 28px;
    border-radius: 14px;
    font-weight: bold;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff9f43, stop:1 #ff7f50);
    margin-top: -2px;
}
QPushButton:pressed {
    background-color: #e15f41;
    margin-top: 2px;
}
QPushButton:disabled {
    background-color: #dfe6e9;
    color: #b2bec3;
}

/* ─── Input Fields ─── */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #ffffff;
    color: #2d3436;
    border: 2px solid #ffeaa7;
    padding: 14px;
    border-radius: 12px;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 2px solid #ff7f50;
    background-color: #fff;
}
QComboBox::drop-down {
    border: none;
    width: 25px;
}
QComboBox QAbstractItemView {
    border: 2px solid #ffeaa7;
    border-radius: 12px;
    background-color: #ffffff;
    selection-background-color: #ff7f50;
    selection-color: #ffffff;
    padding: 5px;
    outline: none;
}

/* ─── Menu Bar ─── */
QMenuBar {
    background-color: #fffbf0;
    padding: 10px;
}
QMenuBar::item {
    padding: 10px 20px;
    border-radius: 8px;
    color: #2d3436;
}
QMenuBar::item:selected {
    background-color: #ff7f50;
    color: #ffffff;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #ffeaa7;
    border-radius: 12px;
    padding: 8px;
}
QMenu::item {
    padding: 12px 24px;
    border-radius: 8px;
}
QMenu::item:selected {
    background-color: #fff0e6;
    color: #ff6b6b;
}

/* ─── Scrollbars (Coral) ─── */
QScrollBar:vertical {
    background-color: transparent;
    width: 14px;
    margin: 4px;
}
QScrollBar::handle:vertical {
    background-color: #ff7f50;
    min-height: 20px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover { background-color: #d35400; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 14px;
    margin: 4px;
}
QScrollBar::handle:horizontal {
    background-color: #ff7f50;
    min-width: 20px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal:hover { background-color: #d35400; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ─── Misc ─── */
QProgressBar {
    background-color: #dfe6e9;
    border-radius: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff7f50, stop:1 #ff6b6b);
    border-radius: 10px;
}
QMessageBox { background-color: #ffffff; }
"""

