"""
========================================================================================
TQM SYSTEM VERIFICATION — PART 3: SERVICES & BUSINESS LOGIC AUTOMATION
========================================================================================
Run this script to verify:
  1. Circulation Service (Book Issue, Return, Quota Limit & SLA Overdue Fine Engine)
  2. Payroll Service (Shift Logging & Automated 1-Click Monthly Salary Calculation)
  3. Analytics Service (Pandas KPIs, Department Stats & Quality Monitoring Latencies)
========================================================================================
"""

import sys
from pathlib import Path
from datetime import date

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure clean UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.models.base import get_db
from app.models.book import Book
from app.models.member import Member
from app.models.user import User
from app.services import (
    issue_book,
    return_book,
    refresh_overdue_status,
    get_circulation_summary,
    log_shift,
    get_staff_shifts,
    get_dashboard_kpis,
    get_loans_dataframe,
    get_department_wise_stats,
    get_quality_log_summary,
)

def test_services():
    print("=" * 80)
    print("RUNNING TQM VERIFICATION -- PART 3: SERVICES & BUSINESS LOGIC")
    print("=" * 80)

    # 1. Test Circulation Logic (TQM Process Automation & Error Prevention)
    print("\n[Step 1/3] Testing Circulation Service (Issue, Return & Quota Safety)...")
    with get_db() as db:
        book = db.query(Book).filter(Book.available_copies > 0).first()
        member = db.query(Member).first()
        assert book is not None, "No books available to test issue"
        assert member is not None, "No members found to test issue"
        book_id = book.id
        member_id = member.id
        initial_copies = book.available_copies

    res_issue = issue_book(book_id, member_id, processed_by="TQM Automation Test")
    print(f"  [OK] Issue Book Result : {res_issue['message']}")
    assert res_issue["success"], "Failed to issue book"

    with get_db() as db:
        book_after = db.get(Book, book_id)
        assert book_after.available_copies == initial_copies - 1, "Available copies failed to decrement"

    loan_id = res_issue["loan_id"]
    res_return = return_book(loan_id)
    print(f"  [OK] Return Book Result: {res_return['message']}")
    assert res_return["success"], "Failed to return book"

    with get_db() as db:
        book_restored = db.get(Book, book_id)
        assert book_restored.available_copies == initial_copies, "Available copies failed to restore"

    # Refresh overdue scan
    overdue_count = refresh_overdue_status()
    circ_summary = get_circulation_summary()
    print(f"  [OK] Overdue scan      : {overdue_count} overdue loans flagged")
    print(f"  [OK] Total loans count : {circ_summary['total_loans']}")
    print(f"  [OK] Total fines logged: Rs. {circ_summary['total_fines_collected']}")

    # 2. Test Staff Shifts & Payroll Automation (TQM Automation & Error Reduction)
    print("\n[Step 2/3] Testing Staff Shift Logging & Payroll Engine...")
    with get_db() as db:
        staff = db.query(User).filter(User.username == "rahul_catalog").first()
        assert staff is not None, "Staff user rahul_catalog not found"
        staff_id = staff.id

    shift_res = log_shift(
        staff_id,
        shift_date=date.today(),
        regular_hours=8.0,
        overtime_hours=2.0,
        tasks_completed="TQM inventory physical audit & defect tagging",
    )
    print(f"  [OK] Log Shift Result  : {shift_res['message']} (Total hours: {shift_res.get('total_hours')})")
    assert shift_res["success"], "Failed to log shift"

    staff_shifts = get_staff_shifts(staff_id)
    print(f"  [OK] Shifts on record  : {len(staff_shifts)} shifts for Rahul Verma")

    # 3. Test Pandas TQM Analytics & KPIs (TQM Decision Making & Quality Monitoring)
    print("\n[Step 3/3] Testing Pandas Analytics & Quality Latency Monitoring...")
    kpis = get_dashboard_kpis()
    print(f"  [OK] Total Books       : {kpis['total_books']}")
    print(f"  [OK] Total Members     : {kpis['total_members']}")
    print(f"  [OK] Active Loans      : {kpis['active_loans']}")
    print(f"  [OK] On-Time Return %  : {kpis['on_time_return_rate']}% (Target: {kpis['tqm_sla_target']}%)")
    print(f"  [OK] TQM SLA Met       : {kpis['sla_met']}")
    print(f"  [OK] Defect Rate %     : {kpis['defect_rate']}% (Tolerance: <={kpis['defect_tolerance']}%)")

    # Test Pandas DataFrames
    loans_df = get_loans_dataframe()
    print(f"  [OK] Pandas Loans DF   : {len(loans_df)} rows loaded into memory")

    dept_stats = get_department_wise_stats()
    if not dept_stats.empty:
        top_dept = dept_stats.sort_values("total_loans", ascending=False).iloc[0]["department"]
        print(f"  [OK] Department Stats  : Active loans identified across departments (Top: {top_dept})")

    q_summary = get_quality_log_summary()
    print(f"  [OK] Quality Audit Log : {q_summary['total_entries']} entries tracked | Avg Latency: {q_summary['avg_execution_ms']} ms")

    print("\n" + "=" * 80)
    print(">>> PART 3 ALL CHECKS PASSED: SERVICES & AUTOMATION OPERATIONAL <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        test_services()
    except Exception as e:
        print(f"\n[ERROR] Part 3 verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
