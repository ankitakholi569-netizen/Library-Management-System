"""
Comprehensive Field Validation Test Suite.
Course: BBAT104 - Total Quality Management.
Verifies error prevention by validating that invalid/missing entries across all fields are properly rejected.
"""

import uuid
import pytest
from database.seed import seed_database
from services.auth_service import create_user, authenticate_user, change_password
from services.library_service import (
    add_book,
    update_book,
    add_member,
    update_member,
    issue_book,
    return_book,
    mark_fine_paid,
)
from services.payroll_service import log_shift, generate_monthly_payroll


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()


def test_book_field_validations():
    u = uuid.uuid4().hex[:6]

    # Empty title
    ok, b, msg = add_book(title="", author="Author", isbn=f"978-1-11111-{u}-1")
    assert not ok and "title" in msg.lower()

    # Short title
    ok, b, msg = add_book(title="A", author="Author", isbn=f"978-1-11111-{u}-2")
    assert not ok and "title" in msg.lower()

    # Empty author
    ok, b, msg = add_book(title="Valid Book", author="", isbn=f"978-1-11111-{u}-3")
    assert not ok and "author" in msg.lower()

    # Empty/short ISBN
    ok, b, msg = add_book(title="Valid Book", author="Valid Author", isbn="")
    assert not ok and "isbn" in msg.lower()
    ok, b, msg = add_book(title="Valid Book", author="Valid Author", isbn="123")
    assert not ok and "isbn" in msg.lower()

    # Invalid publication year
    ok, b, msg = add_book(title="Valid Book", author="Valid Author", isbn=f"978-1-11111-{u}-4", year=500)
    assert not ok and "year" in msg.lower()
    ok, b, msg = add_book(title="Valid Book", author="Valid Author", isbn=f"978-1-11111-{u}-5", year=2500)
    assert not ok and "year" in msg.lower()

    # Invalid total copies
    ok, b, msg = add_book(title="Valid Book", author="Valid Author", isbn=f"978-1-11111-{u}-6", total_copies=0)
    assert not ok and "copies" in msg.lower()

    # Valid book succeeds
    ok, b, msg = add_book(
        title=f"Valid Test Book {u}",
        author="Valid Test Author",
        isbn=f"978-9-{u[:4]}-{u[4:]}-9",
        category="Science",
        year=2024,
        total_copies=5,
        shelf_location="Aisle 5 - Rack B",
    )
    assert ok is True and b is not None
    book_id = b["id"]

    # Updating with invalid data is rejected
    ok, _, msg = update_book(book_id, title="")
    assert not ok
    ok, _, msg = update_book(book_id, author=" ")
    assert not ok
    ok, _, msg = update_book(book_id, year=999)
    assert not ok
    ok, _, msg = update_book(book_id, total_copies=-1)
    assert not ok


def test_member_field_validations():
    u = uuid.uuid4().hex[:6].upper()

    # Empty USN
    ok, m, msg = add_member(usn="", name="John Doe")
    assert not ok and "usn" in msg.lower()

    # Short USN
    ok, m, msg = add_member(usn="AB", name="John Doe")
    assert not ok and "usn" in msg.lower()

    # Empty name
    ok, m, msg = add_member(usn=f"1RV{u}1", name="")
    assert not ok and "name" in msg.lower()

    # Invalid semester
    ok, m, msg = add_member(usn=f"1RV{u}2", name="John Doe", semester=15)
    assert not ok and "semester" in msg.lower()

    # Invalid email format
    ok, m, msg = add_member(usn=f"1RV{u}3", name="John Doe", email="notanemail")
    assert not ok and "email" in msg.lower()

    # Invalid phone format (must be valid 10 digits, not > 10 digits or < 10 digits)
    ok, m, msg = add_member(usn=f"1RV{u}4", name="John Doe", phone="123")
    assert not ok and "phone" in msg.lower()
    ok, m, msg = add_member(usn=f"1RV{u}5", name="John Doe", phone="70178040")  # 8 digits
    assert not ok and "phone" in msg.lower()
    ok, m, msg = add_member(usn=f"1RV{u}6", name="John Doe", phone="988000104222")  # 12 digits (> 10)
    assert not ok and "phone" in msg.lower()
    ok, m, msg = add_member(usn=f"1RV{u}7", name="John Doe", phone="98100030028")  # 11 digits (> 10)
    assert not ok and "phone" in msg.lower()
    ok, m, msg = add_member(usn=f"1RV{u}8", name="John Doe", phone="988000104A")  # non-digits
    assert not ok and "phone" in msg.lower()

    # Valid member creation
    ok, m, msg = add_member(
        usn=f"1RV{u}0",
        name="Valid Student",
        department="CSE",
        semester=4,
        membership_type="Student",
        email=f"valid.{u.lower()}@college.edu",
        phone="9876543210",
    )
    assert ok is True and m is not None
    member_id = m["id"]

    # Updating with invalid email/phone is rejected
    ok, _, msg = update_member(member_id, email="invalid-email")
    assert not ok
    ok, _, msg = update_member(member_id, phone="abc")
    assert not ok
    ok, _, msg = update_member(member_id, phone="988000104222")
    assert not ok
    ok, _, msg = update_member(member_id, phone="12345")
    assert not ok
    ok, _, msg = update_member(member_id, status="InvalidStatus")
    assert not ok


def test_staff_user_validations():
    # Short username
    ok, u, msg = create_user(username="ab", password="password123", full_name="Short User")
    assert not ok and "username" in msg.lower()

    # Invalid characters in username
    ok, u, msg = create_user(username="user name!", password="password123", full_name="Invalid Username")
    assert not ok and "letters, numbers" in msg.lower()

    # Short password
    ok, u, msg = create_user(username="validuser", password="123", full_name="Short Pass")
    assert not ok and "password" in msg.lower()

    # Missing full name
    ok, u, msg = create_user(username="validuser2", password="password123", full_name="")
    assert not ok and "full name" in msg.lower()

    # Invalid hourly rate or salary
    ok, u, msg = create_user(username="validuser3", password="password123", full_name="User", hourly_rate=-10)
    assert not ok and "hourly rate" in msg.lower()
    ok, u, msg = create_user(username="validuser4", password="password123", full_name="User", base_salary=0)
    assert not ok and "salary" in msg.lower()

    # Authentication with empty fields
    ok, _, msg = authenticate_user("", "pass")
    assert not ok and "username is required" in msg.lower()
    ok, _, msg = authenticate_user("admin", "")
    assert not ok and "password is required" in msg.lower()

    # Change password validations
    ok, msg = change_password(1, "", "newpass123")
    assert not ok and "current password is required" in msg.lower()
    ok, msg = change_password(1, "admin123", "short")
    assert not ok and "at least 6 characters" in msg.lower()
    ok, msg = change_password(1, "admin123", "admin123")
    assert not ok and "cannot be the same" in msg.lower()


def test_shift_and_circulation_validations():
    # Invalid user ID for shift
    ok, s, msg = log_shift(user_id=0)
    assert not ok

    # Negative hours
    ok, s, msg = log_shift(user_id=1, regular_hours=-5)
    assert not ok and "negative" in msg.lower()

    # Zero total hours
    ok, s, msg = log_shift(user_id=1, regular_hours=0, overtime_hours=0)
    assert not ok and "greater than zero" in msg.lower()

    # Exceeding 24 hours
    ok, s, msg = log_shift(user_id=1, regular_hours=20, overtime_hours=10)
    assert not ok and "24 hours" in msg.lower()

    # Empty tasks summary
    ok, s, msg = log_shift(user_id=1, regular_hours=8, tasks_completed="")
    assert not ok and "task" in msg.lower()

    # Issue book with invalid IDs
    ok, l, msg = issue_book(book_id=0, member_id=1)
    assert not ok
    ok, l, msg = issue_book(book_id=1, member_id=0)
    assert not ok

    # Return book with invalid ID
    ok, l, msg = return_book(loan_id=0)
    assert not ok

    # Mark fine paid with invalid ID
    ok, msg = mark_fine_paid(loan_id=0)
    assert not ok

    # Payroll invalid month/year
    ok, p, msg = generate_monthly_payroll(user_id=1, period_month=13, period_year=2024)
    assert not ok and "month" in msg.lower()
    ok, p, msg = generate_monthly_payroll(user_id=1, period_month=5, period_year=1800)
    assert not ok and "year" in msg.lower()
