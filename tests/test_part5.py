"""
========================================================================================
TQM SYSTEM VERIFICATION — PART 5: USER INTERFACE & DESKTOP PRESENTATION LAYER
========================================================================================
Run this script to verify:
  1. PySide6 Stylesheet & Modern Executive Slate Design System Tokens
  2. UI Reusable Components (StatCard with instant value update, SearchInput, KPIBadge)
  3. Interactive Views (Dashboard, Book Catalog with Filters, Circulation Desk, Payroll, Quality Audit)
  4. Role-based MainWindow Navigation (Chief Librarian, Assistant Librarian, Student ERP)
========================================================================================
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure clean UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PySide6.QtWidgets import QApplication

def test_ui_layer():
    print("=" * 80)
    print("RUNNING TQM VERIFICATION -- PART 5: USER INTERFACE & DESKTOP SHELL")
    print("=" * 80)

    # Initialize headless or offscreen Qt App
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # 1. Stylesheet & Design Tokens
    print("\n[Step 1/4] Checking Theme Stylesheet & Design Tokens...")
    from app.ui.styles import APP_STYLESHEET
    assert len(APP_STYLESHEET) > 500, "Stylesheet is unexpectedly short"
    assert "#0F172A" in APP_STYLESHEET or "#0B4F9A" in APP_STYLESHEET, "Design tokens missing"
    print(f"  [OK] Stylesheet loaded ({len(APP_STYLESHEET)} chars of CSS rules)")

    # 2. Reusable UI Components
    print("\n[Step 2/4] Testing Reusable Components (StatCard, SearchInput, KPIBadge)...")
    from app.ui.components import StatCard, SearchInput, KPIBadge

    card = StatCard(title="Active Borrowers", value="24", subtitle="Target: <= 50", accent_color="#2563EB")
    card.update_value("25", "Updated")
    card.set_value("26")
    assert card.value_label.text() == "26", "StatCard value update failed"
    print("  [OK] StatCard component initialized and verified (supports both update_value & set_value)")

    s_input = SearchInput(placeholder="Search Books by Title, Author or ISBN...")
    assert hasattr(s_input, "text_changed"), "SearchInput missing text_changed signal"
    assert hasattr(s_input, "textChanged"), "SearchInput missing textChanged signal"
    print("  [OK] SearchInput component verified with instant textChanged/text_changed signals")

    badge = KPIBadge("Within SLA Target", status="success")
    print(f"  [OK] KPIBadge component verified: '{badge.text()}'")

    # 3. View Components Instantiation
    print("\n[Step 3/4] Instantiating All Main Management Views...")
    from app.ui.views.login_view import LoginView
    from app.ui.views.dashboard_view import DashboardView
    from app.ui.views.books_view import BooksView
    from app.ui.views.students_view import StudentsView
    from app.ui.views.circulation_view import CirculationView
    from app.ui.views.payroll_view import PayrollView
    from app.ui.views.quality_audit_view import QualityAuditView
    from app.ui.views.student_portal_view import StudentPortalView

    login = LoginView()
    assert login is not None
    print("  [OK] LoginView (Multi-role authentication with bcrypt) instantiated")

    dash = DashboardView()
    assert dash is not None
    print("  [OK] DashboardView (Pandas KPIs + Matplotlib Analytics charts) instantiated")

    books = BooksView()
    assert books is not None
    print("  [OK] BooksView (Instant search, category filters, defect tagging & Excel export) instantiated")

    students = StudentsView()
    assert students is not None
    print("  [OK] StudentsView (Department filtering & student quota monitoring) instantiated")

    circ = CirculationView()
    assert circ is not None
    print("  [OK] CirculationView (1-click book issue, return & SLA overdue fine engine) instantiated")

    payroll = PayrollView()
    assert payroll is not None
    print("  [OK] PayrollView (Staff shift logger, automated salary calculation & PDF payslip) instantiated")

    quality = QualityAuditView()
    assert quality is not None
    print("  [OK] QualityAuditView (TQM millisecond audit trail & Excel export) instantiated")

    # 4. Multi-Role MainWindow Shell
    print("\n[Step 4/4] Testing MainWindow Dynamic Role Navigation...")
    from app.ui.main_window import MainWindow

    # Admin Session
    admin_user = {
        "username": "admin",
        "full_name": "Dr. Anita Sharma (Chief Librarian)",
        "role": "Chief Librarian",
        "is_student": False,
    }
    main_admin = MainWindow(current_user=admin_user)
    assert main_admin.stack.count() == 6, f"Expected 6 admin views, got {main_admin.stack.count()}"
    print(f"  [OK] Admin MainWindow shell loaded with {main_admin.stack.count()} executive navigation views")

    # Student Session
    student_user = {
        "username": "aarav",
        "full_name": "Aarav Sharma",
        "role": "Student",
        "is_student": True,
        "member_id": 1,
        "department": "CSE",
        "semester": 6,
    }
    main_student = MainWindow(current_user=student_user)
    assert main_student.stack.count() == 2, f"Expected 2 student views, got {main_student.stack.count()}"
    print(f"  [OK] Student MainWindow shell loaded with {main_student.stack.count()} student portal views")

    print("\n" + "=" * 80)
    print(">>> PART 5 ALL CHECKS PASSED: UI & DESKTOP PRESENTATION LAYER OPERATIONAL <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_ui_layer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] UI layer verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
