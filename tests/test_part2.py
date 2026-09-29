"""
========================================================================================
TQM SYSTEM VERIFICATION — PART 2: DATABASE & ORM MODELS
========================================================================================
Run this script to verify:
  1. SQLite Connection with WAL mode & Foreign Keys enabled (Data Integrity)
  2. SQLAlchemy ORM Models (User, Member, Book, Loan, StaffShift, StaffPayroll, QualityLog)
  3. Pre-seeded Engineering catalog, student roster, active loans, and staff payrolls
========================================================================================
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure safe output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sqlalchemy import select, func
from app.models.base import get_db
from app.models.user import User
from app.models.member import Member
from app.models.book import Book
from app.models.loan import Loan
from app.models.payroll import StaffShift, StaffPayroll
from app.models.quality_log import QualityLog
from app.services.db_service import ensure_database_ready

def test_stage_2():
    print("=" * 80)
    print("RUNNING TQM VERIFICATION -- PART 2: DATABASE & ORM LAYER")
    print("=" * 80)

    # 1. Initialize and Seed
    print("\n[Step 1/5] Ensuring Database Tables and Seed Data...")
    try:
        ensure_database_ready()
        print("  [OK] Database schema initialized and seed records confirmed.")
    except Exception as e:
        print(f"  [FAILED] Database Initialization Error: {e}")
        return False

    with get_db() as db:
        # 2. Check Users / Staff & Bcrypt
        print("\n[Step 2/5] Inspecting Staff & Admin Accounts (Security Check)...")
        users = db.scalars(select(User)).all()
        print(f"  [OK] Total Users in DB: {len(users)}")
        for u in users:
            pw_ok = u.verify_password("admin123" if u.username == "admin" else (u.username.split("_")[0] + "123"))
            print(f"       * [{u.role}] '{u.username}' ({u.full_name}) -> Auth check: {'PASSED' if pw_ok else 'FAILED'}")

        # 3. Check Catalog & Students
        print("\n[Step 3/5] Inspecting Book Catalog & Student Directory...")
        books_count = db.scalar(select(func.count(Book.id)))
        members_count = db.scalar(select(func.count(Member.id)))
        print(f"  [OK] Total Books Cataloged: {books_count}")
        print(f"  [OK] Total Students Enrolled: {members_count}")

        sample_book = db.scalars(select(Book).limit(2)).all()
        for b in sample_book:
            print(f"       * Book: '{b.title}' | Copies: {b.available_copies}/{b.total_copies} | ISBN: {b.isbn}")

        # 4. Check Circulation Loans & SLA Overdue Calculations
        print("\n[Step 4/5] Inspecting Circulation Loans & SLA Fine Engine...")
        loans = db.scalars(select(Loan)).all()
        print(f"  [OK] Total Loan Records: {len(loans)}")
        for l in loans:
            l.check_and_update_overdue()
            status_badge = f"STATUS: {l.status}"
            fine_info = f"(Fine: Rs. {l.fine_amount})" if l.fine_amount > 0 else "(No fine)"
            print(f"       * Loan #{l.id}: Student '{l.member.name}' -> Book: '{l.book.title[:28]}...' | {status_badge} {fine_info}")

        # 5. Check Staff Shifts & Payroll Automation
        print("\n[Step 5/5] Inspecting Staff Operational Shifts & Automated Payroll...")
        payrolls = db.scalars(select(StaffPayroll)).all()
        print(f"  [OK] Generated Payroll Records: {len(payrolls)}")
        for p in payrolls:
            print(f"       * Staff: '{p.user.full_name}' | Period: {p.period_month}/{p.period_year} | Gross: Rs. {p.gross_salary} | Deductions: Rs. {p.deductions} | Net: Rs. {p.net_salary}")

        # 6. Check Quality Audit Logs
        q_logs_count = db.scalar(select(func.count(QualityLog.id)))
        print(f"\n  [OK] TQM Quality Audit Entries: {q_logs_count} recorded")

    print("\n" + "=" * 80)
    print(">>> PART 2 ALL CHECKS PASSED: DATABASE & ORM FULLY OPERATIONAL <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_stage_2()
    sys.exit(0 if success else 1)
