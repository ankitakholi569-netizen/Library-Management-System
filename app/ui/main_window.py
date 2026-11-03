"""
app.ui.main_window — backward-compatible MainWindow shim.

Provides a MainWindow with role-based stacked widget counts:
  - Chief Librarian / Library Admin : 6 navigation views
  - Student                         : 2 navigation views
  - Others (default)                : 6 views
"""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QStatusBar,
)
from PySide6.QtCore import Qt, Signal

from gui.styles import APP_STYLESHEET
from gui.dashboard_widget import DashboardWidget
from gui.books_widget import BooksWidget
from gui.members_widget import MembersWidget
from gui.issue_widget import IssueWidget
from gui.employee_widget import EmployeeWidget
from gui.payroll_widget import PayrollWidget
from gui.kiosk_widget import StudentKioskWidget


class MainWindow(QMainWindow):
    """
    Role-aware MainWindow with correct stack counts:
      Admin / Chief Librarian: 6 views (dash, books, members, issue, emp, payroll)
      Student                : 2 views (kiosk, books)
    """

    logout_requested = Signal()

    def __init__(self, current_user: dict | None = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {
            "username": "admin",
            "full_name": "Admin User",
            "role": "Library Admin",
            "is_student": False,
        }
        self.setStyleSheet(APP_STYLESHEET)
        self._setup_ui()

    def _is_student(self) -> bool:
        role = str(self.current_user.get("role", "")).lower()
        return (
            self.current_user.get("is_student", False)
            or "student" in role
        )

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        if self._is_student():
            # 2-view student stack: kiosk + catalog
            self.kiosk_widget = StudentKioskWidget(current_user=self.current_user)
            self.books_widget = BooksWidget(current_user=self.current_user)
            self.stack.addWidget(self.kiosk_widget)   # 0
            self.stack.addWidget(self.books_widget)   # 1
            self.stack.setCurrentIndex(0)
        else:
            # 6-view admin/staff stack
            self.dash_widget    = DashboardWidget()
            self.books_widget   = BooksWidget(current_user=self.current_user)
            self.members_widget = MembersWidget(current_user=self.current_user)
            self.issue_widget   = IssueWidget(current_user=self.current_user)
            self.emp_widget     = EmployeeWidget()
            self.payroll_widget = PayrollWidget()
            self.stack.addWidget(self.dash_widget)     # 0
            self.stack.addWidget(self.books_widget)    # 1
            self.stack.addWidget(self.members_widget)  # 2
            self.stack.addWidget(self.issue_widget)    # 3
            self.stack.addWidget(self.emp_widget)      # 4
            self.stack.addWidget(self.payroll_widget)  # 5
            self.stack.setCurrentIndex(0)

        layout.addWidget(self.stack, 1)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def switch_view(self, index: int):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
