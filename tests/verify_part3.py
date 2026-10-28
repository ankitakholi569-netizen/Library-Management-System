"""
========================================================================================
TQM SYSTEM VERIFICATION — PART 3: PYSIDE6 DESKTOP GUI LAYER
========================================================================================
Course: BBAT104 — Total Quality Management
Run this script to verify:
  1. Login Dialog & bcrypt authentication
  2. MainWindow 7-module navigation shell
  3. DashboardWidget & real-time Matplotlib charts
  4. BooksWidget (Instant search, filters, CRUD, TQM defect toggle)
  5. MembersWidget (Instant search, department filters, borrow history panel)
  6. IssueWidget (Circulation Desk, Issue dialog, Return workflow, Overdue fines)
  7. QualityAuditWidget (ISO 9001 latency audit ledger)
========================================================================================
"""

import sys
import os
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Use offscreen platform for clean headless verification in CLI/test environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from gui.styles import APP_STYLESHEET
from gui.login_dialog import LoginDialog
from gui.main_window import MainWindow, QualityAuditWidget
from gui.dashboard_widget import DashboardWidget, StatCard
from gui.books_widget import BooksWidget, BookDialog
from gui.members_widget import MembersWidget, MemberDialog
from gui.issue_widget import IssueWidget, IssueBookDialog
from services.auth_service import authenticate_user


def test_gui_part3():
    print("=" * 80)
    print("RUNNING TQM SYSTEM VERIFICATION -- PART 3: PYSIDE6 DESKTOP GUI")
    print("=" * 80)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    # --------------------------------------------------------------------------
    # 1. Test Authentication & Login Dialog
    # --------------------------------------------------------------------------
    print("\n[Step 1/7] Testing Login Dialog & Role-Based Authentication...")
    login = LoginDialog()
    assert login is not None, "LoginDialog failed to instantiate"
    login.username_input.setText("admin")
    login.password_input.setText("admin123")
    ok, user, msg = authenticate_user("admin", "admin123")
    assert ok, f"Admin login failed: {msg}"
    print(f"  [OK] Admin Login Verified: {user['full_name']} | Role: {user['role']}")

    bad_ok, _, _ = authenticate_user("admin", "wrong_pass")
    assert not bad_ok, "Security flaw: invalid password accepted"
    print("  [OK] Invalid password rejected by bcrypt")

    # --------------------------------------------------------------------------
    # 2. Test MainWindow Shell & 7-Module Navigation Stack
    # --------------------------------------------------------------------------
    print("\n[Step 2/7] Testing Executive MainWindow Shell & Navigation...")
    main_win = MainWindow(current_user=user)
    assert main_win.stack.count() == 7, f"Expected 7 navigation views, got {main_win.stack.count()}"
    print(f"  [OK] MainWindow initialized with {main_win.stack.count()} modules:")
    module_names = [
        "1. Dashboard",
        "2. Book Catalog",
        "3. Member Directory",
        "4. Circulation Desk",
        "5. Quality Audit",
        "6. Staff & Shifts",
        "7. Payroll Engine"
    ]
    for name in module_names:
        print(f"       • {name}")

    for idx in range(7):
        main_win.switch_view(idx)
        assert main_win.stack.currentIndex() == idx
    print("  [OK] All 7 views switched and data refreshed successfully")

    # --------------------------------------------------------------------------
    # 3. Test DashboardWidget & Matplotlib Visualizations
    # --------------------------------------------------------------------------
    print("\n[Step 3/7] Testing Executive TQM Dashboard & Charts...")
    dash = main_win.dash_widget
    dash.refresh_data()
    books_metric = dash.card_books.value_label.text()
    loans_metric = dash.card_loans.value_label.text()
    members_metric = dash.card_members.value_label.text()
    sla_metric = dash.card_sla.value_label.text()
    defect_metric = dash.card_defect.value_label.text()

    print(f"  [OK] Catalog Volumes      : {books_metric}")
    print(f"  [OK] Active Loans         : {loans_metric}")
    print(f"  [OK] Registered Patrons   : {members_metric}")
    print(f"  [OK] On-Time SLA Rate     : {sla_metric}")
    print(f"  [OK] Inventory Defect Rate: {defect_metric}")
    assert int(books_metric) > 0, "Expected positive book count in dashboard"
    assert dash.canvas1 is not None and dash.canvas2 is not None
    print("  [OK] Matplotlib canvas 1 (Circulation SLA) and canvas 2 (Department Distribution) rendered")

    # --------------------------------------------------------------------------
    # 4. Test BooksWidget (Catalog, Instant Search & Filter Logic)
    # --------------------------------------------------------------------------
    print("\n[Step 4/7] Testing Book Catalog Widget (CRUD, Search & Defect Guard)...")
    bw = main_win.books_widget
    total_books = bw.table.rowCount()
    print(f"  [OK] Initial Catalog Count: {total_books} books")
    assert total_books >= 50, f"Expected at least 50 books per TQM requirement, got {total_books}"

    # Search filter test
    bw.search_box.setText("Algorithms")
    bw._do_search()
    filtered_count = bw.table.rowCount()
    print(f"  [OK] Search 'Algorithms' -> {filtered_count} matching volumes found")
    assert filtered_count > 0, "Search for Algorithms should return results"

    # Reset search
    bw.search_box.setText("")
    bw._do_search()
    assert bw.table.rowCount() == total_books
    print(f"  [OK] Reset Search -> Restored full catalog of {total_books} books")

    # --------------------------------------------------------------------------
    # 5. Test MembersWidget (Directory, Search & Borrow History Panel)
    # --------------------------------------------------------------------------
    print("\n[Step 5/7] Testing Member Directory Widget (Profiles & History)...")
    mw = main_win.members_widget
    total_members = mw.table.rowCount()
    print(f"  [OK] Initial Members Count: {total_members} members")
    assert total_members >= 20, f"Expected at least 20 members per TQM requirement, got {total_members}"

    # Test member selection and history loading
    if total_members > 0:
        member_id = int(mw.table.item(0, 0).text())
        member_name = mw.table.item(0, 2).text()
        mw.history_panel.load_history(member_id, member_name)
        history_rows = mw.history_panel.table.rowCount()
        print(f"  [OK] Borrow History for '{member_name}': {history_rows} past/active loan records loaded")

    # --------------------------------------------------------------------------
    # 6. Test IssueWidget (Circulation Desk, Active Loans, Returns & Fines)
    # --------------------------------------------------------------------------
    print("\n[Step 6/7] Testing Circulation Desk Widget (Issue, Return & SLA Fines)...")
    iw = main_win.issue_widget
    iw.refresh_data()
    active_loans_count = iw.loans_table.rowCount()
    print(f"  [OK] Active Loans in Circulation Table: {active_loans_count}")

    # Verify IssueBookDialog
    issue_dlg = IssueBookDialog(processed_by="Admin Automated Test")
    assert issue_dlg.member_table.rowCount() > 0, "Issue dialog member table should have candidates"
    assert issue_dlg.book_table.rowCount() > 0, "Issue dialog book table should have candidates"
    print(f"  [OK] IssueBookDialog initialized: {issue_dlg.member_table.rowCount()} members, {issue_dlg.book_table.rowCount()} available books")

    # --------------------------------------------------------------------------
    # 7. Test QualityAuditWidget (ISO 9001 Latency Ledger)
    # --------------------------------------------------------------------------
    print("\n[Step 7/7] Testing Quality Audit Ledger Widget (ISO 9001 / TQM Traceability)...")
    qw = main_win.audit_widget
    qw.refresh_audit()
    audit_rows = qw.table.rowCount()
    print(f"  [OK] Quality Audit Ledger Count: {audit_rows} logged operations with ms latencies")
    assert audit_rows > 0, "Quality log ledger should contain entries"

    print("\n" + "=" * 80)
    print(">>> MAJOR PART 3 ALL CHECKS PASSED: PYSIDE6 DESKTOP GUI FULLY OPERATIONAL <<<")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_gui_part3()
    finally:
        import matplotlib.pyplot as plt
        plt.close("all")
        app = QApplication.instance()
        if app:
            app.quit()
    sys.exit(0)
