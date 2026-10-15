"""
StatCard Component — Modern KPI Display Card.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

class StatCard(QFrame):
    """Clean metric card with large value, description, and status indicator."""

    def __init__(self, title: str, value: str, subtitle: str = "", accent_color: str = "#2563EB", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setProperty("class", "card")
        self.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                border-left: 5px solid {accent_color};
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        # Title
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: #0F172A; font-size: 26px; font-weight: bold; margin-top: 2px;")
        layout.addWidget(self.value_label)

        # Subtitle
        if subtitle:
            self.sub_label = QLabel(subtitle)
            self.sub_label.setStyleSheet("color: #64748B; font-size: 11px; margin-top: 2px;")
            layout.addWidget(self.sub_label)
        else:
            self.sub_label = None

    def update_value(self, value: str, subtitle: str = None):
        self.value_label.setText(str(value))
        if subtitle and self.sub_label:
            self.sub_label.setText(subtitle)
