"""
app.services.report_service — backward-compatible shim for report generation.
Wraps real services.report_service and extends signatures to accept pre-fetched list data.
"""
from __future__ import annotations
from typing import Optional, List
from datetime import datetime

from services.report_service import (
    generate_payslip_pdf,
    generate_catalog_excel as _real_catalog_excel,
    generate_quality_audit_excel as _real_audit_excel,
    _ensure_exports_dir,
    EXPORTS_DIR,
)


def generate_payslip_pdf(
    staff_name: str,
    period: str,
    gross: float,
    deductions: float,
    net: float,
    regular_hours: float = 0.0,
    overtime_hours: float = 0.0,
    hourly_rate: float = 0.0,
) -> str:
    """Delegate to real payslip generator."""
    from services.report_service import generate_payslip_pdf as _real_payslip
    return _real_payslip(
        staff_name=staff_name,
        period=period,
        gross=gross,
        deductions=deductions,
        net=net,
        regular_hours=regular_hours,
        overtime_hours=overtime_hours,
        hourly_rate=hourly_rate,
    )


def generate_catalog_excel(
    books_data_or_category=None,
    output_filename: Optional[str] = None,
) -> str:
    """
    Extended generate_catalog_excel.
    Accepts either:
      - A list of book dicts  (legacy test_part4.py usage)
      - A category str filter (original usage)
      - Nothing               (export all)
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    # If called with a pre-fetched list, write directly
    if isinstance(books_data_or_category, list):
        books_data = books_data_or_category
        _ensure_exports_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"catalog_report_{timestamp}.xlsx"
        filepath = str(EXPORTS_DIR / filename)

        wb = Workbook()
        ws = wb.active
        ws.title = "Textbook Inventory"

        header_font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
        header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        # Build columns from whatever keys the dicts have
        if books_data:
            col_keys = list(books_data[0].keys())
        else:
            col_keys = ["id", "title", "author", "isbn", "category", "total_copies", "available_copies", "defect_flag"]

        for col_idx, header in enumerate(col_keys, 1):
            cell = ws.cell(row=1, column=col_idx, value=header.replace("_", " ").title())
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        for row_idx, book in enumerate(books_data, 2):
            for col_idx, key in enumerate(col_keys, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=str(book.get(key, "")))
                cell.border = thin_border

        # Auto-adjust
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 3, 12), 40)

        wb.save(filepath)
        return filepath

    # Otherwise delegate to real function (category filter or None)
    return _real_catalog_excel(
        category=books_data_or_category,
        output_filename=output_filename,
    )


def generate_quality_audit_excel(
    logs_data_or_limit=None,
    output_filename: Optional[str] = None,
) -> str:
    """
    Extended generate_quality_audit_excel.
    Accepts either:
      - A list of log dicts  (legacy test_part4.py usage)
      - An int limit         (original usage)
      - Nothing              (export all, limit=200)
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    # If called with pre-fetched list, write directly
    if isinstance(logs_data_or_limit, list):
        logs_data = logs_data_or_limit
        _ensure_exports_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"quality_audit_{timestamp}.xlsx"
        filepath = str(EXPORTS_DIR / filename)

        wb = Workbook()
        ws = wb.active
        ws.title = "TQM Audit Ledger"

        header_font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        if logs_data:
            col_keys = list(logs_data[0].keys())
        else:
            col_keys = ["id", "timestamp", "module", "action", "status", "execution_time_ms", "details", "remedial_action"]

        for col_idx, header in enumerate(col_keys, 1):
            cell = ws.cell(row=1, column=col_idx, value=header.replace("_", " ").title())
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        for row_idx, item in enumerate(logs_data, 2):
            for col_idx, key in enumerate(col_keys, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=str(item.get(key, "")))
                cell.border = thin_border

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 3, 12), 40)

        wb.save(filepath)
        return filepath

    # Delegate to real function
    limit = logs_data_or_limit if isinstance(logs_data_or_limit, int) else 200
    return _real_audit_excel(limit=limit, output_filename=output_filename)
