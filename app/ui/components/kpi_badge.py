"""
KPIBadge Component — Color-Coded Status Pill.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class KPIBadge(QLabel):
    """Badge pill for status values (e.g. Overdue, Available, Returned)."""

    SCHEMES = {
        "success": ("#ECFDF5", "#065F46", "#A7F3D0"),
        "danger":  ("#FEF2F2", "#991B1B", "#FECACA"),
        "warning": ("#FFFBEB", "#92400E", "#FDE68A"),
        "info":    ("#EFF6FF", "#1E40AF", "#BFDBFE"),
        "neutral": ("#F1F5F9", "#334155", "#CBD5E1"),
    }

    def __init__(self, text: str, scheme: str = "neutral", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_scheme(scheme)

    def set_scheme(self, scheme: str):
        bg, text_color, border = self.SCHEMES.get(scheme, self.SCHEMES["neutral"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {text_color};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
