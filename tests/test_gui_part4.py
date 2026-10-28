"""
Verification script for PySide6 Desktop GUI Layer.
"""

import sys
import os
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Use offscreen platform for clean headless testing in CI/test environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

def test_gui_layer():
    print("=" * 70)
    print("VERIFYING PYSIDE6 DESKTOP GUI LAYER")
    print("=" * 70)

    app = QApplication.instance() or QApplication(sys.argv)

    # 1. Stylesheet Verification
    print("\n[Step 1/6] Testing QSS Stylesheet & Modern Theme Tokens...")
    from gui.styles import APP_STYLESHEET
    assert len(APP_STYLESHEET) > 500, "Stylesheet is unexpectedly short"
    assert "#0F172A" in APP_STYLESHEET, "Design tokens missing"
    print(f"  [OK] Theme stylesheet loaded ({len(APP_STYLESHEET)} chars of CSS rules)")

    # 2. Dashboard Widget Verification
    print("\n[Step 2/6] Testing DashboardWidget (KPI Cards + Matplotlib Charts)...")
    from gui.dashboard_widget import DashboardWidget, StatCard
    card = StatCard("Test Metric", "42", "Active", "#2563EB")
    card.update_value("43", "Updated")
    assert card.value_label.text() == "43"
    print("  [OK] StatCard component verified")

    dash = DashboardWidget()
    assert dash is not None
    assert dash.card_books.value_label.text() != ""
    print(f"  [OK] DashboardWidget initialized with live metrics (Books: {dash.card_books.value_label.text()})")

    # 3. Core Library Widgets Verification
    print("\n[Step 3/6] Testing BooksWidget, MembersWidget & IssueWidget...")
    from gui.books_widget import BooksWidget
    from gui.members_widget import MembersWidget
    from gui.issue_widget import IssueWidget

    bw = BooksWidget()
    assert bw.table.rowCount() > 0, "BooksWidget table should display seeded books"
    print(f"  [OK] BooksWidget initialized ({bw.table.rowCount()} books in catalog)")

    mw = MembersWidget()
    assert mw.table.rowCount() > 0, "MembersWidget table should display seeded members"
    print(f"  [OK] MembersWidget initialized ({mw.table.rowCount()} members loaded)")

    iw = IssueWidget()
    assert iw.loans_table.rowCount() > 0, "IssueWidget loans table should display active loans"
    print(f"  [OK] IssueWidget initialized ({iw.loans_table.rowCount()} circulation loans loaded)")

    # 4. Employee & Payroll Widget Verification
    print("\n[Step 4/6] Testing EmployeeWidget & PayrollWidget...")
    from gui.employee_widget import EmployeeWidget
    from gui.payroll_widget import PayrollWidget
    emp_widget = EmployeeWidget()
    assert emp_widget is not None
    assert emp_widget.staff_table.rowCount() > 0
    print(f"  [OK] EmployeeWidget initialized ({emp_widget.staff_table.rowCount()} staff accounts loaded)")

    payroll_widget = PayrollWidget()
    assert payroll_widget is not None
    assert payroll_widget.payroll_table.rowCount() > 0
    print(f"  [OK] PayrollWidget initialized ({payroll_widget.payroll_table.rowCount()} payroll records in ledger)")

    # 5. MainWindow Navigation Shell Verification
    print("\n[Step 5/6] Testing MainWindow Shell & Navigation Switching...")
    from gui.main_window import MainWindow
    main_win = MainWindow(current_user={
        "username": "admin",
        "full_name": "Dr. Anita Sharma",
        "role": "Chief Librarian"
    })
    assert main_win.stack.count() == 7, f"Expected 7 views in stack, got {main_win.stack.count()}"
    print(f"  [OK] MainWindow shell initialized with {main_win.stack.count()} navigation views")

    for i in range(7):
        main_win.switch_view(i)
        assert main_win.stack.currentIndex() == i
    print("  [OK] Navigation view switching across all 7 modules confirmed")

    # 6. Quality Audit Widget Verification
    print("\n[Step 6/6] Testing QualityAuditWidget (ISO 9001 Latency Ledger)...")
    from gui.main_window import QualityAuditWidget
    audit_widget = QualityAuditWidget()
    assert audit_widget.table.rowCount() > 0
    print(f"  [OK] QualityAuditWidget initialized ({audit_widget.table.rowCount()} audit log entries loaded)")

    print("\n" + "=" * 70)
    print(">>> DESKTOP GUI FULLY OPERATIONAL (ALL CHECKS PASSED) <<<")
    print("=" * 70)

if __name__ == "__main__":
    test_gui_layer()
    os._exit(0)
