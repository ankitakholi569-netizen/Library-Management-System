"""
app.ui.components — backward-compatible UI component shims.
StatCard, SearchInput, KPIBadge are real, fully functional widgets.
"""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QLineEdit
from PySide6.QtCore import Qt, Signal


class StatCard(QFrame):
    """
    Reusable KPI Stat Card widget.
    Accepts: title, value, subtitle, accent_color
    """

    def __init__(
        self,
        title: str = "",
        value: str = "—",
        subtitle: str = "",
        accent_color: str = "#2563EB",
        parent=None,
    ):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: 10px;
                border-left: 4px solid {accent_color};
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {accent_color};")
        self.value_label.setAlignment(Qt.AlignLeft)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("font-size: 11px; color: #94A3B8;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def update_value(self, value: str, subtitle: str = ""):
        """Update displayed value and subtitle."""
        self.value_label.setText(str(value))
        if subtitle:
            self.subtitle_label.setText(subtitle)

    def set_value(self, value: str):
        """Alias for compatibility."""
        self.value_label.setText(str(value))


class SearchInput(QLineEdit):
    """Instant search input with text_changed signal alias."""

    text_changed = Signal(str)

    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px 14px;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus { border-color: #2563EB; }
        """)
        self.textChanged.connect(self.text_changed.emit)


class KPIBadge(QLabel):
    """Colored status badge for KPI displays."""

    _STATUS_COLORS = {
        "success": ("#166534", "#DCFCE7"),
        "warning": ("#92400E", "#FEF3C7"),
        "danger":  ("#991B1B", "#FEE2E2"),
        "info":    ("#1E40AF", "#DBEAFE"),
    }

    def __init__(self, text: str = "", status: str = "info", parent=None):
        super().__init__(text, parent)
        fg, bg = self._STATUS_COLORS.get(status, self._STATUS_COLORS["info"])
        self.setStyleSheet(
            f"color: {fg}; background: {bg}; border-radius: 12px; "
            f"padding: 2px 10px; font-size: 11px; font-weight: 700;"
        )
