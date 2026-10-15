"""
Verification Script -- Part 3: Services & Business Logic Automation.
Verifies Circulation Service, Payroll Engine, and Analytics Service.
"""

import sys
from datetime import date
from app.services.circulation_service import issue_book, return_book, refresh_overdue_status, get_circulation_summary
from app.services.payroll_service import log_shift
from app.services.analytics_service import get_dashboard_kpis, get_loans_dataframe
from app.models.base import get_db
from app.models.book import Book
from app.models.member import Member
from app.models.user import User

def test_services():
    print("=" * 80)
    print("RUNNING TQM VERIFICATION -- PART 3: SERVICES & BUSINESS LOGIC")
    print("=" * 80)

    # 1. Test Analytics KPIs
    print("\n[Step 1/3] Testing TQM Analytics & KPIs...")
    kpis = get_dashboard_kpis()
    print(f"  [OK] Total Books       : {kpis['total_books']}")
    print(f"  [OK] Total Members     : {kpis['total_members']}")
    print(f"  [OK] Active Loans      : {kpis['active_loans']}")
    print(f"  [OK] On-Time Return %  : {kpis['on_time_return_rate']}% (Target: {kpis['tqm_sla_target']}%)")
    print(f"  [OK] TQM SLA Met       : {kpis['sla_met']}")
    assert kpis["total_books"] > 0, "No books found"

    # 2. Test Circulation Logic
    print("\n[Step 2/3] Testing Circulation Service (Issue & Return)...")
    with get_db() as db:
        book = db.query(Book).filter(Book.available_copies > 0).first()
        member = db.query(Member).first()
        book_id = book.id
        member_id = member.id
        initial_copies = book.available_copies

    res_issue = issue_book(book_id, member_id, processed_by="Test Runner")
    print(f"  [OK] Issue Book Result : {res_issue['message']}")
    assert res_issue["success"], "Failed to issue book"

    with get_db() as db:
        book_after = db.get(Book, book_id)
        assert book_after.available_copies == initial_copies - 1, "Copy count did not decrement"

    loan_id = res_issue["loan_id"]
    res_return = return_book(loan_id)
    print(f"  [OK] Return Book Result: {res_return['message']}")
    assert res_return["success"], "Failed to return book"

    with get_db() as db:
        book_restored = db.get(Book, book_id)
        assert book_restored.available_copies == initial_copies, "Copy count did not restore"

    circ_summary = get_circulation_summary()
    print(f"  [OK] Total circulation transactions: {circ_summary['total_loans']}")

    # 3. Test Staff Shifts & Payroll Service
    print("\n[Step 3/3] Testing Staff Shift Logging & Payroll...")
    with get_db() as db:
        staff = db.query(User).filter(User.username == "rahul_catalog").first()
        staff_id = staff.id

    shift_res = log_shift(staff_id, shift_date=date.today(), regular_hours=8.0, overtime_hours=2.0, tasks_completed="Inventory auditing")
    print(f"  [OK] Log Shift Result  : {shift_res['message']} (Total hours: {shift_res.get('total_hours')})")
    assert shift_res["success"], "Failed to log shift"

    print("\n" + "=" * 80)
    print(">>> PART 3 ALL CHECKS PASSED: SERVICES OPERATIONAL <<<")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_services()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
