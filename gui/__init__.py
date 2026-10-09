"""
GUI package for Library Management System (TQM Edition).
Course: BBAT104.
Exports modern PySide6 desktop widgets and the main executive navigation shell.
"""

from gui.styles import APP_STYLESHEET
from gui.login_dialog import LoginDialog
from gui.dashboard_widget import DashboardWidget, StatCard
from gui.books_widget import BooksWidget, BookDialog
from gui.members_widget import MembersWidget, MemberDialog, BorrowHistoryPanel
from gui.issue_widget import IssueWidget, IssueBookDialog
from gui.employee_widget import EmployeeWidget, AddStaffDialog, LogShiftDialog
from gui.payroll_widget import PayrollWidget
from gui.main_window import MainWindow, QualityAuditWidget, CatalogWidget

__all__ = [
    "APP_STYLESHEET",
    "LoginDialog",
    "DashboardWidget",
    "StatCard",
    "BooksWidget",
    "BookDialog",
    "MembersWidget",
    "MemberDialog",
    "BorrowHistoryPanel",
    "IssueWidget",
    "IssueBookDialog",
    "EmployeeWidget",
    "AddStaffDialog",
    "LogShiftDialog",
    "PayrollWidget",
    "MainWindow",
    "QualityAuditWidget",
    "CatalogWidget",
]
