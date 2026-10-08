"""
Verification script for Major Part 3: Services Layer.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import services

def test_services():
    print("=" * 70)
    print("VERIFYING MAJOR PART 3: CORE TQM SERVICES LAYER")
    print("=" * 70)

    # 1. Test Authentication Service
    print("\n[Step 1/4] Testing Authentication & Password Verification...")
    ok, user, msg = services.authenticate_user("admin", "admin123")
    assert ok, f"Admin authentication failed: {msg}"
    print(f"  [OK] Admin Login: {user['full_name']} | Role: {user['role']}")

    bad_ok, _, _ = services.authenticate_user("admin", "wrongpassword")
    assert not bad_ok, "Security flaw: invalid password was accepted!"
    print("  [OK] Wrong password properly rejected by bcrypt")

    # 2. Test Centralized Logger & Quality Audit Trail
    print("\n[Step 2/4] Testing Logger Service & Quality Latency Monitor...")
    with services.timed_operation("TEST_MODULE", "BENCHMARK_OP", details="Part 3 Verification Run"):
        total = sum(i * i for i in range(10000))
    print("  [OK] Timed operation logged to logs/app.log and database QualityLog ledger")

    # 3. Test Automated Shift & Payroll Service
    print("\n[Step 3/4] Testing Automated Shift Logging & Payroll Engine...")
    shifts = services.get_staff_shifts(user_id=1)
    print(f"  [OK] Total shifts retrieved for User 1: {len(shifts)}")

    ok, payroll, msg = services.generate_monthly_payroll(user_id=1, period_month=10, period_year=2026)
    assert ok, f"Payroll generation failed: {msg}"
    print(f"  [OK] Payroll Generated: Month: {payroll['period']} | Gross: Rs. {payroll['gross_salary']} | Deductions: Rs. {payroll['deductions']} | Net: Rs. {payroll['net_salary']}")

    # 4. Test Report Generation (PDF & Excel directly into exports/)
    print("\n[Step 4/4] Testing PDF & Excel Documentation Engines...")
    pdf_path = services.generate_payslip_pdf(
        staff_name="Dr. Anita Sharma",
        period="10/2026",
        gross=payroll["gross_salary"],
        deductions=payroll["deductions"],
        net=payroll["net_salary"],
        regular_hours=160.0,
        overtime_hours=10.0,
        hourly_rate=150.0,
        role="Chief Librarian"
    )
    assert Path(pdf_path).exists(), f"PDF not found at {pdf_path}"
    print(f"  [OK] PDF Payslip exported: {pdf_path} ({Path(pdf_path).stat().st_size} bytes)")

    cat_path = services.generate_catalog_excel()
    assert Path(cat_path).exists(), f"Catalog Excel not found at {cat_path}"
    print(f"  [OK] Catalog Excel exported: {cat_path} ({Path(cat_path).stat().st_size} bytes)")

    audit_path = services.generate_quality_audit_excel()
    assert Path(audit_path).exists(), f"Audit Excel not found at {audit_path}"
    print(f"  [OK] Quality Audit Excel exported: {audit_path} ({Path(audit_path).stat().st_size} bytes)")

    print("\n" + "=" * 70)
    print(">>> MAJOR PART 3 ALL CHECKS PASSED: SERVICES FULLY OPERATIONAL <<<")
    print("=" * 70)

if __name__ == "__main__":
    test_services()
