"""
Services package for Library Management System (TQM Edition).
Course: BBAT104 — Total Quality Management.

Exports all business logic, security, library CRUD, search, automated payroll,
centralized logging, and reporting services.

Architecture rule: GUI and web routes import ONLY from this package.
No business logic in gui/ or web/ files.
"""

# ── Logging & Quality ──────────────────────────────────────────────────────
from services.logger_service import (
    get_logger,
    log_quality_event,
    timed_operation,
)

# ── Authentication & Access Control ───────────────────────────────────────
from services.auth_service import (
    hash_password,
    verify_password,
    authenticate_user,
    create_user,
    change_password,
    get_all_users,
    get_staff_users,
    ROLE_CHIEF_LIBRARIAN,
    ROLE_ASSISTANT_LIBRARIAN,
    ROLE_LIBRARY_ASSISTANT,
    ROLE_STUDENT,
)

# ── Core Library: Books, Members, Issue/Return, Fines ─────────────────────
from services.library_service import (
    # Books
    get_all_books,
    get_book_by_id,
    get_book_categories,
    add_book,
    update_book,
    delete_book,
    # Members
    get_all_members,
    get_member_by_id,
    get_member_departments,
    add_member,
    update_member,
    delete_member,
    get_member_loan_history,
    # Issue / Return / Fines
    issue_book,
    return_book,
    mark_fine_paid,
    get_all_loans,
    refresh_overdue_statuses,
    # Dashboard KPIs
    get_dashboard_kpis,
    get_popular_books,
    get_monthly_issue_trend,
)

# ── Search & Retrieval (Quality Goal 1) ───────────────────────────────────
from services.search_service import (
    quick_search,
    search_books,
    search_members,
    search_loans,
    get_search_kpi_summary,
)

# ── Staff Payroll & Shift Tracking ────────────────────────────────────────
from services.payroll_service import (
    log_shift,
    get_staff_shifts,
    generate_monthly_payroll,
    generate_all_staff_payrolls,
    get_all_payrolls,
    get_payroll_by_id,
    update_payroll_status,
)

# ── Reports & Exports ─────────────────────────────────────────────────────
from services.report_service import (
    generate_payslip_pdf,
    generate_catalog_excel,
    generate_quality_audit_excel,
    generate_circulation_report_excel,
    generate_inventory_report_pdf,
    generate_overdue_fines_report_pdf,
)

__all__ = [
    # Logging
    "get_logger", "log_quality_event", "timed_operation",
    # Auth
    "hash_password", "verify_password", "authenticate_user",
    "create_user", "change_password", "get_all_users", "get_staff_users",
    "ROLE_CHIEF_LIBRARIAN", "ROLE_ASSISTANT_LIBRARIAN",
    "ROLE_LIBRARY_ASSISTANT", "ROLE_STUDENT",
    # Library — Books
    "get_all_books", "get_book_by_id", "get_book_categories",
    "add_book", "update_book", "delete_book",
    # Library — Members
    "get_all_members", "get_member_by_id", "get_member_departments",
    "add_member", "update_member", "delete_member", "get_member_loan_history",
    # Library — Circulation
    "issue_book", "return_book", "mark_fine_paid",
    "get_all_loans", "refresh_overdue_statuses",
    # Library — Dashboard KPIs
    "get_dashboard_kpis", "get_popular_books", "get_monthly_issue_trend",
    # Search
    "quick_search", "search_books", "search_members",
    "search_loans", "get_search_kpi_summary",
    # Payroll
    "log_shift", "get_staff_shifts", "generate_monthly_payroll",
    "generate_all_staff_payrolls", "get_all_payrolls",
    "get_payroll_by_id", "update_payroll_status",
    # Reports
    "generate_payslip_pdf", "generate_catalog_excel",
    "generate_quality_audit_excel", "generate_circulation_report_excel",
    "generate_inventory_report_pdf", "generate_overdue_fines_report_pdf",
]
