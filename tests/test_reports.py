"""
Unit Test Suite for PDF & Excel Report Services (Quality Goal 2: Documentation Support).
Course: BBAT104 - Total Quality Management.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from database.seed import seed_database
from services.report_service import (
    generate_payslip_pdf,
    generate_catalog_excel,
    generate_quality_audit_excel,
    generate_circulation_report_excel,
    generate_inventory_report_pdf,
    generate_overdue_fines_report_pdf,
)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()

def test_generate_payslip_pdf():
    pdf_path = generate_payslip_pdf(
        staff_name="Dr. Anita Sharma",
        period="10/2026",
        gross=24000.0,
        deductions=1200.0,
        net=22800.0,
        regular_hours=160.0,
        overtime_hours=8.0,
        hourly_rate=150.0,
        role="Chief Librarian",
        output_filename="test_payslip_sample.pdf",
    )
    p = Path(pdf_path)
    assert p.exists()
    assert p.stat().st_size > 1500  # ReportLab PDF header + tables > 1.5KB

def test_generate_catalog_excel():
    excel_path = generate_catalog_excel(output_filename="test_catalog_sample.xlsx")
    p = Path(excel_path)
    assert p.exists()
    assert p.stat().st_size > 2000

def test_generate_quality_audit_excel():
    audit_path = generate_quality_audit_excel(limit=50, output_filename="test_audit_sample.xlsx")
    p = Path(audit_path)
    assert p.exists()
    assert p.stat().st_size > 2000

def test_generate_circulation_report_excel():
    circ_path = generate_circulation_report_excel(output_filename="test_circ_sample.xlsx")
    p = Path(circ_path)
    assert p.exists()
    assert p.stat().st_size > 2000

def test_generate_inventory_report_pdf():
    inv_pdf = generate_inventory_report_pdf(output_filename="test_inventory_summary.pdf")
    p = Path(inv_pdf)
    assert p.exists()
    assert p.stat().st_size > 1500

def test_generate_overdue_fines_report_pdf():
    fines_pdf = generate_overdue_fines_report_pdf(output_filename="test_overdue_fines.pdf")
    p = Path(fines_pdf)
    assert p.exists()
    assert p.stat().st_size > 1500

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
