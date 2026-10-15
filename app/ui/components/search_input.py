"""
SearchInput Component — Styled Search Box with Instant Filtering and Clear Button.
"""

from PySide6.QtWidgets import QLineEdit, QToolButton
from PySide6.QtCore import Qt, Signal

class SearchInput(QLineEdit):
    """Modern Search Input Field with clear button and smooth styling."""

    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 1.5px solid #2563EB;
                background-color: #F8FAFC;
            }
        """)
