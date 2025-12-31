"""Custom widgets and delegates for the Embedded Tracker GUI.

This module contains specialized Qt widgets and item delegates
for enhanced visual presentation and user interaction.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, Property, QRectF, QEvent
from PySide6.QtGui import QPainter, QBrush, QColor, QPainterPath
from PySide6.QtWidgets import (
    QPushButton,
    QWidget,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

__all__ = [
    "StatusDelegate",
    "RippleButton",
    "STATUS_COLORS",
]


# Status color mapping for pill badges
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
        """Paint status as a colored pill badge."""
        text = index.data(Qt.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return

        status = str(text).lower().replace(" ", "_")
        color = STATUS_COLORS.get(status)

        # Fallback lookups for partial matches
        if not color and "working" in status:
            color = STATUS_COLORS["working"]
        elif not color and "break" in status:
            color = STATUS_COLORS["break"]
        elif not color and "pause" in status:
            color = STATUS_COLORS["paused"]
        elif not color and "complete" in status:
            color = STATUS_COLORS["completed"]

        if color:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            # Setup rect for pill with padding
            rect = QRectF(option.rect).adjusted(8, 4, -8, -4)

            # Draw pill background
            path = QPainterPath()
            path.addRoundedRect(rect, 10, 10)
            painter.fillPath(path, color)

            # Draw text in white, bold
            painter.setPen(Qt.white)
            font = option.font
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, int(Qt.AlignCenter), str(text).title())

            painter.restore()
        else:
            super().paint(painter, option, index)


class RippleButton(QPushButton):
    """Material Design-style button with ripple animation on click."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self._radius = 0.0
        self._pos = QPoint(0, 0)
        self._anim = QPropertyAnimation(self, b"radius_prop", self)
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutQuad)

    @Property(float)
    def radius_prop(self) -> float:
        """Get current ripple radius."""
        return self._radius

    @radius_prop.setter
    def radius_prop(self, r: float) -> None:
        """Set ripple radius and trigger repaint."""
        self._radius = r
        self.update()

    def mousePressEvent(self, event: QEvent) -> None:
        """Start ripple animation from click position."""
        self._pos = event.pos()
        self._radius = 0.0
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(max(self.width(), self.height()) * 1.5)
        self._anim.start()
        super().mousePressEvent(event)

    def paintEvent(self, event: QEvent) -> None:
        """Paint button with ripple overlay."""
        super().paintEvent(event)
        if self._radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            # Semi-transparent white ripple
            brush = QBrush(QColor(255, 255, 255, 60))
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self._pos, self._radius, self._radius)
