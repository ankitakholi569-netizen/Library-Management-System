"""
Main Window — Executive Application Shell & Navigation for CampusLib Pro.
Demonstrates TQM Principle: Customer Focus, Usability & Integrated System Architecture.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget,
    QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from app.ui.views.dashboard_view import DashboardView
from app.ui.views.books_view import BooksView
from app.ui.views.circulation_view import CirculationView
from app.ui.views.payroll_view import PayrollView
from app.ui.views.quality_audit_view import QualityAuditView
from app.core.logger import get_logger

logger = get_logger("ui.main")


class MainWindow(QMainWindow):
    """Main Application Window with Executive Sidebar Navigation and Views Stack."""

    logout_requested = Signal()

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("CampusLib Pro • TQM Library & Staff Management System")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)

        self._setup_ui()
        self._navigate(0)  # Start on Dashboard

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(240)
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(12, 16, 12, 16)
        s_layout.setSpacing(6)

        # Brand
        brand_lbl = QLabel("CampusLib Pro")
        brand_lbl.setObjectName("sidebarLogo")
        s_layout.addWidget(brand_lbl)

        version_lbl = QLabel("TQM Edition • v2.0.0")
        version_lbl.setObjectName("sidebarSublogo")
        s_layout.addWidget(version_lbl)

        # User Badge
        user_card = QFrame()
        user_card.setObjectName("sidebarUserBadge")
        u_layout = QVBoxLayout(user_card)
        u_layout.setContentsMargins(10, 8, 10, 8)
        u_layout.setSpacing(2)

        name_lbl = QLabel(self.current_user.get("full_name", "Staff Member"))
        name_lbl.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 12px;")
        role_lbl = QLabel(self.current_user.get("role", "Staff"))
        role_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        u_layout.addWidget(name_lbl)
        u_layout.addWidget(role_lbl)
        s_layout.addWidget(user_card)

        s_layout.addSpacing(14)

        # Navigation Buttons
        self.nav_buttons = []
        nav_items = [
            ("📊  Executive Dashboard", 0),
            ("📚  Book Catalog", 1),
            ("🔄  Circulation Desk", 2),
            ("💼  Staff & Payroll", 3),
            ("🛡️  Quality Audit Trail", 4),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=index: self._navigate(idx))
            self.nav_buttons.append(btn)
            s_layout.addWidget(btn)

        s_layout.addStretch()

        # Logout Button
        logout_btn = QPushButton("🚪  Sign Out")
        logout_btn.setProperty("class", "nav-btn")
        logout_btn.setStyleSheet("""
            QPushButton {
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 6px;
                padding: 8px 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.15);
                color: #FFFFFF;
            }
        """)
        logout_btn.clicked.connect(self._handle_logout)
        s_layout.addWidget(logout_btn)

        main_layout.addWidget(sidebar)

        # 2. Main Content Area (Stacked Widget)
        self.stack = QStackedWidget()

        self.dashboard_view = DashboardView()
        self.books_view = BooksView()
        self.circulation_view = CirculationView()
        self.payroll_view = PayrollView()
        self.quality_view = QualityAuditView()

        self.stack.addWidget(self.dashboard_view)     # Index 0
        self.stack.addWidget(self.books_view)         # Index 1
        self.stack.addWidget(self.circulation_view)   # Index 2
        self.stack.addWidget(self.payroll_view)       # Index 3
        self.stack.addWidget(self.quality_view)       # Index 4

        main_layout.addWidget(self.stack)

        # 3. Status Bar
        status = QStatusBar()
        status_text = f"Connected: campus_tqm.db (WAL Mode)  |  TQM SLA: 14-Day Loan  |  Active User: {self.current_user.get('full_name')} ({self.current_user.get('role')})"
        status.showMessage(status_text)
        self.setStatusBar(status)

    def _navigate(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

        # Auto-refresh target view on navigation
        if index == 0:
            self.dashboard_view.refresh_data()
        elif index == 1:
            self.books_view.load_books()
        elif index == 2:
            self.circulation_view.load_loans()
        elif index == 3:
            self.payroll_view.load_data()
        elif index == 4:
            self.quality_view.load_audit_logs()

    def _handle_logout(self):
        reply = QMessageBox.question(
            self, "Sign Out", "Are you sure you want to end your session?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            logger.info(f"User '{self.current_user.get('username')}' logged out.")
            self.logout_requested.emit()
            self.close()
