"""
Verification Script -- Part 4: Reports & Document Generation.
Verifies PDF Pay Slip creation and Excel Catalog Export.
"""

import sys
import os
from pathlib import Path
from app.services.report_service import generate_payslip_pdf, generate_catalog_excel
from app.models.base import get_db
from app.models.book import Book

def test_reports():
    print("=" * 80)
    print("RUNNING TQM VERIFICATION -- PART 4: REPORTS GENERATION")
    print("=" * 80)

    # 1. Test PDF Payslip Generation
    print("\n[Step 1/2] Generating Sample PDF Pay Slip...")
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
    assert os.path.getsize(pdf_path) > 500, "PDF file is suspiciously small"

    # 2. Test Excel Catalog Report Generation
    print("\n[Step 2/2] Generating Excel Book Catalog Export...")
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

    excel_path = generate_catalog_excel(books_data)
    print(f"  [OK] Generated Excel File: {excel_path}")
    assert os.path.exists(excel_path), "Excel file was not created"
    assert os.path.getsize(excel_path) > 1000, "Excel file is suspiciously small"

    print("\n" + "=" * 80)
    print(">>> PART 4 ALL CHECKS PASSED: REPORT ENGINE OPERATIONAL <<<")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_reports()
    except Exception as e:
        print(f"\n[ERROR] Report verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
