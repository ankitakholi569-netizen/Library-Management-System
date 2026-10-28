"""
Unit Test Suite for Issue, Return, and Fine Calculation (Quality SLA Compliance).
Course: BBAT104 - Total Quality Management.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from database.seed import seed_database
from services.library_service import (
    issue_book,
    return_book,
    mark_fine_paid,
    get_all_loans,
    refresh_overdue_statuses,
    get_book_by_id,
    get_member_by_id,
    get_all_books,
    get_all_members,
)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()

def test_successful_book_issue_and_inventory_decrement():
    all_books = get_all_books()
    all_members = get_all_members()
    target_book = next(b for b in all_books if b["available_copies"] > 1)
    target_member = next(m for m in all_members if m["borrowed_count"] == 0)

    initial_avail = target_book["available_copies"]
    initial_borrowed = target_member["borrowed_count"]

    ok, loan_res, msg = issue_book(book_id=target_book["id"], member_id=target_member["id"], processed_by="admin")
    assert ok is True
    loan_id = loan_res["id"] if isinstance(loan_res, dict) else loan_res

    # Check updated book & member counts
    updated_book = get_book_by_id(target_book["id"])
    updated_member = get_member_by_id(target_member["id"])
    assert updated_book["available_copies"] == initial_avail - 1
    assert updated_member["borrowed_count"] == initial_borrowed + 1

    # Now return the book
    ret_ok, fine, ret_msg = return_book(loan_id=loan_id, processed_by="admin")
    assert ret_ok is True

    # Check inventory restored
    restored_book = get_book_by_id(target_book["id"])
    restored_member = get_member_by_id(target_member["id"])
    assert restored_book["available_copies"] == initial_avail
    assert restored_member["borrowed_count"] == initial_borrowed

def test_issue_rejected_when_quota_or_status_invalid():
    all_members = get_all_members()
    target_member = all_members[0]
    from database.db import get_db
    from database.models import Member
    with get_db() as db:
        m = db.get(Member, target_member["id"])
        m.status = "Suspended"
        db.commit()

    ok, loan_id, msg = issue_book(book_id=1, member_id=target_member["id"], processed_by="admin")
    assert ok is False
    assert "suspended" in msg.lower() or "cannot" in msg.lower() or "quota" in msg.lower()

    # Restore
    with get_db() as db:
        m = db.get(Member, target_member["id"])
        m.status = "Active"
        db.commit()

def test_refresh_overdue_statuses_and_fines():
    # Test batch overdue status updater
    updated_count = refresh_overdue_statuses()
    assert isinstance(updated_count, int)

    loans = get_all_loans()
    assert len(loans) > 0
    overdue_loans = [l for l in loans if l["status"] == "Overdue"]
    for ol in overdue_loans:
        assert ol["fine_amount"] >= 0.0

def test_mark_fine_paid():
    loans = get_all_loans()
    overdue_loans = [l for l in loans if l["status"] == "Overdue" and not l["fine_paid"]]
    if overdue_loans:
        target_loan = overdue_loans[0]
        ok, msg = mark_fine_paid(target_loan["id"], processed_by="admin")
        assert ok is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
