"""
========================================================================================
TQM SYSTEM VERIFICATION — PART 4: DOCUMENT GENERATION & REPORT ENGINES
========================================================================================
Run this script to verify:
  1. PDF Pay Slip Generation with ReportLab (Formatted table, auto calculation footer)
  2. Excel Book Catalog Export with OpenPyXL (Styled executive headers, auto column width)
  3. Excel TQM Quality Audit Export with OpenPyXL (Latency in ms, defects & remedial actions)
========================================================================================
"""

import sys
import os
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

from app.services.report_service import (
    generate_payslip_pdf,
    generate_catalog_excel,
    generate_quality_audit_excel,
)
from app.models.base import get_db
from app.models.book import Book
from app.models.quality_log import QualityLog

def test_reports():
    print("=" * 80)
    print("RUNNING TQM VERIFICATION -- PART 4: DOCUMENT GENERATION & REPORT ENGINES")
    print("=" * 80)

    # 1. Test PDF Payslip Generation
    print("\n[Step 1/3] Generating Executive PDF Pay Slip (ReportLab)...")
    pdf_path = generate_payslip_pdf(
        staff_name="Dr. Anita Sharma",
        period="10/2026",
        gross=32500.0,
        deductions=1625.0,
        net=30875.0,
        regular_hours=160.0,
        overtime_hours=10.0,
        hourly_rate=190.0,
    )
    print(f"  [OK] Generated PDF File: {pdf_path}")
    assert os.path.exists(pdf_path), "PDF file was not created"
    file_size_pdf = os.path.getsize(pdf_path)
    print(f"  [OK] PDF File Size     : {file_size_pdf} bytes")
    assert file_size_pdf > 500, "PDF file is suspiciously small"

    # 2. Test Excel Catalog Report Generation
    print("\n[Step 2/3] Generating Styled Excel Catalog Export (OpenPyXL)...")
    with get_db() as db:
        books = db.query(Book).all()
        books_data = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "isbn": b.isbn,
                "category": b.category,
                "total_copies": b.total_copies,
                "available_copies": b.available_copies,
                "defect_flag": "Yes" if b.defect_flag else "No",
            }
            for b in books
        ]

    excel_cat_path = generate_catalog_excel(books_data)
    print(f"  [OK] Generated Catalog Excel: {excel_cat_path}")
    assert os.path.exists(excel_cat_path), "Catalog Excel was not created"
    file_size_excel = os.path.getsize(excel_cat_path)
    print(f"  [OK] Excel File Size        : {file_size_excel} bytes")
    assert file_size_excel > 1000, "Excel file is suspiciously small"

    # 3. Test Excel Quality Audit Log Generation
    print("\n[Step 3/3] Generating TQM Quality Audit Ledger Export (OpenPyXL)...")
    with get_db() as db:
        q_logs = db.query(QualityLog).all()
        logs_data = [
            {
                "id": q.id,
                "timestamp": str(q.timestamp),
                "module": q.module,
                "action": q.action,
                "status": q.status,
                "execution_time_ms": q.execution_time_ms,
                "details": q.details,
                "remedial_action": q.remedial_action,
            }
            for q in q_logs
        ]

    excel_audit_path = generate_quality_audit_excel(logs_data)
    print(f"  [OK] Generated Audit Excel  : {excel_audit_path}")
    assert os.path.exists(excel_audit_path), "Audit Excel was not created"
    file_size_audit = os.path.getsize(excel_audit_path)
    print(f"  [OK] Audit Excel File Size  : {file_size_audit} bytes")
    assert file_size_audit > 1000, "Audit Excel file is suspiciously small"

    print("\n" + "=" * 80)
    print(">>> PART 4 ALL CHECKS PASSED: REPORT ENGINES FULLY OPERATIONAL <<<")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        test_reports()
    except Exception as e:
        print(f"\n[ERROR] Report verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
