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
from gui.kiosk_widget import StudentKioskWidget, FacultyResearchWidget
from gui.stock_widget import StockLedgerWidget, DailyZReportWidget
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
            "username": "rahul_catalog",
            "full_name": "Rahul Verma",
            "role": "Library Assistant",
        }
        self.setWindowTitle(f"{APP_NAME} (v{APP_VERSION}) — {COURSE_NAME}")
        self.resize(1300, 850)
        self.setStyleSheet(APP_STYLESHEET)
        self._setup_ui()

    @property
    def stakeholder_persona(self) -> str:
        role = str(self.current_user.get("role", "")).lower()
        uname = str(self.current_user.get("username", "")).lower()
        if "student" in role or "rohit" in uname:
            return "Student (Kiosk)"
        elif "faculty" in role or "prof" in uname:
            return "Faculty Member"
        elif "circulation" in role or "priya" in uname:
            return "Circulation Staff"
        elif "catalog" in role or "rahul" in uname:
            return "Catalog Manager"
        else:
            return "Library Admin"

    @property
    def is_admin(self) -> bool:
        return self.stakeholder_persona == "Library Admin"

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Navigation Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(250)
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

        # Persona Header Banner
        persona = self.stakeholder_persona
        persona_tag = QLabel(f"STAKEHOLDER: {persona.upper()}")
        persona_tag.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: 800; letter-spacing: 0.8px; padding-top: 10px; padding-left: 6px;")
        side_layout.addWidget(persona_tag)

        # Right Content Stack
        self.stack = QStackedWidget()

        # Instantiate All Widgets
        self.dash_widget = DashboardWidget()
        self.books_widget = BooksWidget(current_user=self.current_user)
        self.catalog_widget = self.books_widget  # Alias
        self.members_widget = MembersWidget(current_user=self.current_user)
        self.issue_widget = IssueWidget(current_user=self.current_user)
        self.audit_widget = QualityAuditWidget()
        self.emp_widget = EmployeeWidget()
        self.payroll_widget = PayrollWidget()
        self.kiosk_widget = StudentKioskWidget(current_user=self.current_user)
        self.faculty_widget = FacultyResearchWidget(current_user=self.current_user)
        self.stock_widget = StockLedgerWidget(current_user=self.current_user)
        self.z_report_widget = DailyZReportWidget(current_user=self.current_user)

        # Add all to stack
        self.stack.addWidget(self.dash_widget)          # 0: Dashboard
        self.stack.addWidget(self.books_widget)         # 1: Books
        self.stack.addWidget(self.members_widget)       # 2: Members
        self.stack.addWidget(self.issue_widget)         # 3: Issue
        self.stack.addWidget(self.audit_widget)         # 4: Audit
        self.stack.addWidget(self.emp_widget)           # 5: Shifts
        self.stack.addWidget(self.payroll_widget)       # 6: Payroll
        self.stack.addWidget(self.kiosk_widget)         # 7: Student Kiosk (FR-01)
        self.stack.addWidget(self.faculty_widget)       # 8: Faculty Research (FR-02)
        self.stack.addWidget(self.stock_widget)         # 9: Stock Ledger (FR-04)
        self.stack.addWidget(self.z_report_widget)      # 10: Daily Z-Report (FR-05)

        # Tailor Navigation Buttons to Persona
        self.nav_buttons = []

        if persona == "Student (Kiosk)":
            nav_items = [
                ("🖥️ Student Kiosk (Ctrl+K)", 7),
                ("📚 Textbook Catalog", 1),
            ]
            default_view = 7
        elif persona == "Faculty Member":
            nav_items = [
                ("🔬 Research & Citations", 8),
                ("📚 Catalog & Journals", 1),
            ]
            default_view = 8
        elif persona == "Circulation Staff":
            nav_items = [
                ("🔄 POS Circulation Bay", 3),
                ("📚 Book Catalog", 1),
                ("👥 Member Directory", 2),
                ("📊 Activity Dashboard", 0),
            ]
            default_view = 3
        elif persona == "Catalog Manager":
            nav_items = [
                ("📦 Stock Ledger & GRN", 9),
                ("📚 Catalog Maintenance", 1),
                ("📊 Inventory Dashboard", 0),
            ]
            default_view = 9
        else:  # Library Admin
            nav_items = [
                ("📊 Executive Dashboard", 0),
                ("📚 Book Catalog", 1),
                ("👥 Member Directory", 2),
                ("🔄 Circulation Desk", 3),
                ("📦 Stock Ledger (FR-04)", 9),
                ("🧾 Daily Z-Report (FR-05)", 10),
                ("📈 21 CFR Part 11 Audit", 4),
                ("👤 Staff Shifts", 5),
                ("💰 Payroll Engine", 6),
            ]
            default_view = 0

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, target=idx: self.switch_view(target))
            side_layout.addWidget(btn)
            self.nav_buttons.append((btn, idx))

        side_layout.addStretch()

        # User Profile Block
        user_frame = QFrame()
        user_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 10px;")
        u_layout = QVBoxLayout(user_frame)
        u_layout.setSpacing(2)
        u_name = QLabel(self.current_user.get("full_name", "Rahul Verma"))
        u_name.setStyleSheet("color: white; font-weight: 700; font-size: 12px;")
        u_role = QLabel(f"Role: {self.current_user.get('role', 'Library Assistant')}")
        u_role.setStyleSheet("color: #94A3B8; font-size: 11px;")
        u_spec = QLabel(f"Stakeholder: {persona}")
        u_spec.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: 600;")
        u_layout.addWidget(u_name)
        u_layout.addWidget(u_role)
        u_layout.addWidget(u_spec)
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
        main_layout.addWidget(self.stack, 1)

        # Switch to Persona Default View
        self.switch_view(default_view)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(
            f"Connected to SQLite Database (WAL Mode) • TQM Quality SLA Active • Logged in: {self.current_user.get('full_name')} ({persona})"
        )

    def switch_view(self, index: int):
        self.stack.setCurrentIndex(index)
        for btn, idx in self.nav_buttons:
            btn.setChecked(idx == index)
            btn.setProperty("active", "true" if idx == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh data when switching to widgets
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh_data"):
            widget.refresh_data()
        elif hasattr(widget, "refresh_audit"):
            widget.refresh_audit()
        elif hasattr(widget, "refresh_search"):
            widget.refresh_search()
        elif hasattr(widget, "refresh_ledger"):
            widget.refresh_ledger()
        elif hasattr(widget, "refresh_z_report"):
            widget.refresh_z_report()

    def _handle_logout(self):
        self.logout_requested.emit()
        self.close()
