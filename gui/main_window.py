"""
Main Window Shell for Library Management System (TQM Edition).
Course: BBAT104 - Total Quality Management.

Hosts the PySide6 Executive Desktop Shell with role-based navigation,
instant search filters, embedded analytics, book & member CRUD,
circulation desk (issue/return), staff shift tracking, and payroll processing.
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStatusBar,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from sqlalchemy import select

from config.settings import APP_NAME, APP_VERSION, COURSE_NAME
from database.db import get_db
from database.models import QualityLog
from gui.styles import APP_STYLESHEET
from gui.dashboard_widget import DashboardWidget
from gui.books_widget import BooksWidget
from gui.members_widget import MembersWidget
from gui.issue_widget import IssueWidget
from gui.employee_widget import EmployeeWidget
from gui.payroll_widget import PayrollWidget
from services.report_service import generate_quality_audit_excel
from services.logger_service import get_logger

logger = get_logger("gui.main_window")

# Backward compatibility alias
CatalogWidget = BooksWidget


# ==============================================================================
# TQM QUALITY AUDIT & CONTINUOUS IMPROVEMENT LEDGER WIDGET
# ==============================================================================
class QualityAuditWidget(QWidget):
    """
    Quality Audit Trail Ledger with millisecond response benchmarking
    and corrective action tracking (ISO 9001/TQM Principle).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_audit()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("TQM Continuous Improvement & Quality Ledger")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub = QLabel("Traceability audit trail, millisecond latency benchmarking & standard corrective actions (ISO 9001/TQM)")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.export_audit_btn = QPushButton("📊 Export Audit Ledger (Excel)")
        self.export_audit_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600; padding: 8px 16px; border-radius: 6px;")
        self.export_audit_btn.clicked.connect(self._export_excel)
        header.addWidget(self.export_audit_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Timestamp (UTC)", "Module", "Action", "Status", "Latency (ms)", "Remedial SOP Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def refresh_audit(self):
        with get_db() as db:
            logs = db.scalars(select(QualityLog).order_by(QualityLog.timestamp.desc()).limit(100)).all()
            data = [l.to_dict() for l in logs]

        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(item["timestamp"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["module"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["action"]))

            status_item = QTableWidgetItem(item["status"])
            if "SUCCESS" in item["status"]:
                status_item.setForeground(Qt.darkGreen)
            elif "BREACH" in item["status"] or "WARN" in item["status"]:
                status_item.setForeground(Qt.darkYellow)
            else:
                status_item.setForeground(Qt.darkRed)
            self.table.setItem(row, 4, status_item)

            self.table.setItem(row, 5, QTableWidgetItem(f"{item['execution_time_ms']:.2f} ms"))
            self.table.setItem(row, 6, QTableWidgetItem(item["remedial_action"]))

    def _export_excel(self):
        path = generate_quality_audit_excel()
        QMessageBox.information(self, "Audit Export", f"Quality audit ledger exported:\n\n{path}")


# ==============================================================================
# EXECUTIVE DESKTOP MAIN WINDOW
# ==============================================================================
class MainWindow(QMainWindow):
    """
    Unified Executive Desktop Shell for the Library Management System.
    Connects all 7 core modules with responsive navigation and live telemetry.
    """

    logout_requested = Signal()

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {
            "username": "admin",
            "full_name": "Dr. Anita Sharma",
            "role": "Chief Librarian",
        }
        self.setWindowTitle(f"{APP_NAME} (v{APP_VERSION}) — {COURSE_NAME}")
        self.resize(1300, 850)
        self.setStyleSheet(APP_STYLESHEET)
        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Navigation Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 16, 10, 16)
        side_layout.setSpacing(6)

        # Logo / Title
        logo = QLabel("CampusLib Pro")
        logo.setObjectName("sidebarLogo")
        sublogo = QLabel(f"TQM Edition • {COURSE_NAME}")
        sublogo.setObjectName("sidebarSublogo")
        side_layout.addWidget(logo)
        side_layout.addWidget(sublogo)

        # Navigation Buttons (All 7 Core Modules)
        self.nav_buttons = []
        nav_items = [
            ("📊 Dashboard", 0),
            ("📚 Book Catalog", 1),
            ("👥 Member Directory", 2),
            ("🔄 Circulation Desk", 3),
            ("📈 Quality Audit", 4),
            ("👤 Staff & Shifts", 5),
            ("💰 Payroll Engine", 6),
        ]

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, target=idx: self.switch_view(target))
            side_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        side_layout.addStretch()

        # User Profile Block
        user_frame = QFrame()
        user_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 10px;")
        u_layout = QVBoxLayout(user_frame)
        u_layout.setSpacing(2)
        u_name = QLabel(self.current_user.get("full_name", "User"))
        u_name.setStyleSheet("color: white; font-weight: 700; font-size: 12px;")
        u_role = QLabel(self.current_user.get("role", "Staff"))
        u_role.setStyleSheet("color: #94A3B8; font-size: 11px;")
        u_layout.addWidget(u_name)
        u_layout.addWidget(u_role)
        side_layout.addWidget(user_frame)

        # Logout Button
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #EF4444;
                border: 1px solid #EF4444;
                padding: 6px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        self.logout_btn.clicked.connect(self._handle_logout)
        side_layout.addWidget(self.logout_btn)

        main_layout.addWidget(sidebar)

        # 2. Right Content Stack
        self.stack = QStackedWidget()

        self.dash_widget = DashboardWidget()
        self.books_widget = BooksWidget(current_user=self.current_user)
        self.catalog_widget = self.books_widget  # Backward compatibility alias
        self.members_widget = MembersWidget(current_user=self.current_user)
        self.issue_widget = IssueWidget(current_user=self.current_user)
        self.audit_widget = QualityAuditWidget()
        self.emp_widget = EmployeeWidget()
        self.payroll_widget = PayrollWidget()

        self.stack.addWidget(self.dash_widget)       # 0
        self.stack.addWidget(self.books_widget)      # 1
        self.stack.addWidget(self.members_widget)    # 2
        self.stack.addWidget(self.issue_widget)      # 3
        self.stack.addWidget(self.audit_widget)      # 4
        self.stack.addWidget(self.emp_widget)        # 5
        self.stack.addWidget(self.payroll_widget)    # 6

        main_layout.addWidget(self.stack, 1)

        # Default View: Dashboard
        self.switch_view(0)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(
            f"Connected to SQLite Database (WAL Mode) • TQM Quality SLA Active • Logged in: {self.current_user.get('full_name')} ({self.current_user.get('role')})"
        )

    def switch_view(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh data when switching to widgets
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh_data"):
            widget.refresh_data()
        elif hasattr(widget, "refresh_audit"):
            widget.refresh_audit()

    def _handle_logout(self):
        self.logout_requested.emit()
        self.close()
