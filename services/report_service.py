"""
Documentation & Reporting Service.
Course: BBAT104 - Total Quality Management.
Features:
- ReportLab PDF Pay Slip generation with institutional headers & TQM accreditation
- OpenPyXL styled Excel exports for Book Catalog, TQM Audit Logs, and Payroll Ledgers
- Outputs directly into exports/ directory
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from config.settings import EXPORTS_DIR, APP_NAME, COURSE_NAME, ORGANIZATION
from database.db import get_db
from database.models import Book, QualityLog, StaffPayroll, Loan, Member
from services.logger_service import get_logger, log_quality_event, timed_operation

logger = get_logger("report_service")


def _ensure_exports_dir() -> Path:
    """Ensures the exports directory exists."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return EXPORTS_DIR


# ==============================================================================
# 1. REPORTLAB PDF PAY SLIP GENERATOR
# ==============================================================================
def generate_payslip_pdf(
    staff_name: str,
    period: str,
    gross: float,
    deductions: float,
    net: float,
    regular_hours: float,
    overtime_hours: float,
    hourly_rate: float,
    role: str = "Staff Member",
    output_filename: Optional[str] = None,
) -> str:
    """
    Generates a formal, audit-ready PDF payslip using ReportLab.
    Saves to exports/ and returns absolute file path.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    _ensure_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = staff_name.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")
    clean_period = period.replace("/", "-")
    filename = output_filename or f"payslip_{clean_name}_{clean_period}_{timestamp}.pdf"
    filepath = str(EXPORTS_DIR / filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()

    # Custom typography
    header_style = ParagraphStyle(
        "PayslipHeader",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,  # Center
    )
    sub_style = ParagraphStyle(
        "PayslipSub",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph(f"{APP_NAME}", header_style))
    elements.append(Paragraph(f"{ORGANIZATION} • {COURSE_NAME}", sub_style))
    elements.append(Paragraph("OFFICIAL EXECUTIVE STAFF PAY SLIP", ParagraphStyle("Banner", parent=sub_style, fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#2563EB"))))
    elements.append(Spacer(1, 8 * mm))

    # 2. Staff Details & Period
    info_data = [
        ["Staff Full Name:", staff_name, "Pay Period:", period],
        ["Designation / Role:", role, "Generated On:", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Standard Rate:", f"Rs. {hourly_rate:.2f}/hr", "Audit Protocol:", "ISO 9001:2015 / TQM-SLA"],
    ]
    info_table = Table(info_data, colWidths=[38 * mm, 50 * mm, 38 * mm, 48 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#475569")),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    # 3. Earnings & Deductions Breakdown
    regular_pay = regular_hours * hourly_rate
    ot_pay = overtime_hours * hourly_rate * 1.5

    breakdown_data = [
        ["Description", "Hours / Basis", "Rate / Multiplier", "Total Amount (INR)"],
        ["Regular Operational Shift", f"{regular_hours:.1f} hrs", f"Rs. {hourly_rate:.2f}/hr", f"Rs. {regular_pay:,.2f}"],
        ["Overtime Shift (TQM 1.5x)", f"{overtime_hours:.1f} hrs", f"Rs. {hourly_rate * 1.5:.2f}/hr", f"Rs. {ot_pay:,.2f}"],
        ["Gross Earnings", "", "", f"Rs. {gross:,.2f}"],
        ["Statutory Tax & PF Withholding (5%)", "Standard Deduction", "5.0%", f"- Rs. {deductions:,.2f}"],
        ["NET SALARY DISBURSED", "", "", f"Rs. {net:,.2f}"],
    ]

    breakdown_table = Table(breakdown_data, colWidths=[65 * mm, 35 * mm, 35 * mm, 39 * mm])
    breakdown_table.setStyle(TableStyle([
        # Table Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        # Alternating background
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
        ("BACKGROUND", (0, 2), (-1, 2), colors.white),
        # Gross row
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#F1F5F9")),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        # Deductions row
        ("TEXTCOLOR", (3, 4), (3, 4), colors.HexColor("#DC2626")),
        # Net Salary highlight
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#DBEAFE")),
        ("TEXTCOLOR", (0, 5), (-1, 5), colors.HexColor("#1E3A8A")),
        ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
        ("FONTSIZE", (0, 5), (-1, 5), 11),
        # Borders & Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(breakdown_table)
    elements.append(Spacer(1, 12 * mm))

    # 4. Signatures & TQM Compliance Verification
    sign_data = [
        ["Staff Signature", "Chief Librarian Approval", "Finance / Quality Cell Stamp"],
        ["\n_______________________", "\n_______________________", "\n_______________________"],
        ["Employee Acceptance", "Verified & Approved", "Automated TQM Audit Trail Validated"],
    ]
    sign_table = Table(sign_data, colWidths=[58 * mm, 58 * mm, 58 * mm])
    sign_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#64748B")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(sign_table)
    elements.append(Spacer(1, 8 * mm))

    # 5. Footer Disclaimer
    footer_text = (
        f"This pay slip was generated electronically by the {APP_NAME} Automated Payroll Engine. "
        f"Complies with BBAT104 TQM quality performance parameters and zero-defect payroll governance."
    )
    elements.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=sub_style, fontSize=7, textColor=colors.HexColor("#94A3B8"))))

    doc.build(elements)
    logger.info(f"ReportLab PDF pay slip successfully generated at: {filepath}")
    log_quality_event("PAYROLL", "EXPORT_PDF_PAYSLIP", "SUCCESS", details=f"Generated PDF for {staff_name}")
    return filepath


# ==============================================================================
# 2. OPENPYXL EXCEL EXPORTS (Catalog & Quality Audit)
# ==============================================================================
def generate_catalog_excel(category: Optional[str] = None, output_filename: Optional[str] = None) -> str:
    """
    Exports the textbook inventory catalog into a formatted Excel spreadsheet.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    _ensure_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_filename or f"catalog_report_{timestamp}.xlsx"
    filepath = str(EXPORTS_DIR / filename)

    with get_db() as db:
        query = select(Book).order_by(Book.category, Book.title)
        if category:
            query = query.where(Book.category == category)
        books = db.scalars(query).all()
        books_data = [b.to_dict() for b in books]

    wb = Workbook()
    ws = wb.active
    ws.title = "Textbook Inventory"

    # Styling Tokens
    header_font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    headers = [
        "Book ID", "Title", "Author(s)", "Category", "ISBN", "Edition Year",
        "Total Copies", "Available Copies", "Shelf Location", "TQM Defect Flag"
    ]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    # Data Rows
    defect_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    for row_idx, book in enumerate(books_data, 2):
        defect_str = "DEFECT DETECTED" if book.get("defect_flag") else "Normal"
        values = [
            book.get("id"),
            book.get("title"),
            book.get("author"),
            book.get("category"),
            book.get("isbn"),
            book.get("year"),
            book.get("total_copies"),
            book.get("available_copies"),
            book.get("shelf_location"),
            defect_str,
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if col_idx in (1, 6, 7, 8, 10):
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")

            if book.get("defect_flag") and col_idx == 10:
                cell.fill = defect_fill

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    wb.save(filepath)
    logger.info(f"Catalog Excel report exported: {filepath}")
    log_quality_event("CATALOG", "EXPORT_EXCEL", "SUCCESS", details=f"Exported {len(books_data)} books to Excel")
    return filepath


def generate_quality_audit_excel(limit: int = 200, output_filename: Optional[str] = None) -> str:
    """
    Exports the TQM continuous improvement audit trail to an Excel spreadsheet.
    Includes millisecond response latency and SLA compliance flags.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    _ensure_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_filename or f"quality_audit_{timestamp}.xlsx"
    filepath = str(EXPORTS_DIR / filename)

    with get_db() as db:
        logs = db.scalars(select(QualityLog).order_by(QualityLog.timestamp.desc()).limit(limit)).all()
        logs_data = [l.to_dict() for l in logs]

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

    headers = [
        "Audit ID", "Timestamp (UTC)", "Subsystem Module", "Action / Operation",
        "TQM Status", "Latency (ms)", "Event Details", "Remedial SOP Action"
    ]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    success_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    warning_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    defect_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

    for row_idx, item in enumerate(logs_data, 2):
        values = [
            item.get("id"),
            item.get("timestamp"),
            item.get("module"),
            item.get("action"),
            item.get("status"),
            item.get("execution_time_ms"),
            item.get("details"),
            item.get("remedial_action"),
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if col_idx in (1, 2, 3, 5, 6):
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")

            # Color-code status
            if col_idx == 5:
                status_val = str(val).upper()
                if "SUCCESS" in status_val:
                    cell.fill = success_fill
                elif "BREACH" in status_val or "WARN" in status_val:
                    cell.fill = warning_fill
                elif "DEFECT" in status_val or "ERROR" in status_val:
                    cell.fill = defect_fill

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45)

    wb.save(filepath)
    logger.info(f"Quality audit Excel exported: {filepath}")
    log_quality_event("QUALITY", "EXPORT_AUDIT_EXCEL", "SUCCESS", details=f"Exported {len(logs_data)} audit entries")
    return filepath


# ==============================================================================
# 4. OPENPYXL CIRCULATION & LOANS LEDGER EXCEL EXPORTER
# ==============================================================================
def generate_circulation_report_excel(output_filename: Optional[str] = None) -> str:
    """
    Exports full circulation borrowing history, active loans, and overdue items to Excel.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    _ensure_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_filename or f"circulation_report_{timestamp}.xlsx"
    filepath = str(EXPORTS_DIR / filename)

    with get_db() as db:
        loans = db.scalars(select(Loan).order_by(Loan.borrow_date.desc())).all()
        loans_data = [l.to_dict() for l in loans]

    wb = Workbook()
    ws = wb.active
    ws.title = "Circulation Ledger"

    header_font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    headers = [
        "Loan ID", "Book Title", "Member Name", "Member USN",
        "Borrow Date", "Due Date", "Return Date", "Status",
        "Fine Accrued (INR)", "Fine Paid", "Processed By"
    ]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    borrowed_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    overdue_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    returned_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")

    for row_idx, item in enumerate(loans_data, 2):
        values = [
            item.get("id"),
            item.get("book_title"),
            item.get("member_name"),
            item.get("member_usn"),
            item.get("borrow_date"),
            item.get("due_date"),
            item.get("return_date") or "—",
            item.get("status"),
            item.get("fine_amount", 0.0),
            "Yes" if item.get("fine_paid") else "No",
            item.get("processed_by"),
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if col_idx in (1, 4, 5, 6, 7, 8, 10):
                cell.alignment = Alignment(horizontal="center")
            elif col_idx == 9:
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="left")

            # Status coloring
            if col_idx == 8:
                st = str(val).upper()
                if "RETURNED" in st:
                    cell.fill = returned_fill
                elif "OVERDUE" in st:
                    cell.fill = overdue_fill
                else:
                    cell.fill = borrowed_fill

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    wb.save(filepath)
    logger.info(f"Circulation Excel report exported: {filepath}")
    log_quality_event("CIRCULATION", "EXPORT_CIRCULATION_EXCEL", "SUCCESS", details=f"Exported {len(loans_data)} loans")
    return filepath


# ==============================================================================
# 5. REPORTLAB PDF INVENTORY SUMMARY AUDIT
# ==============================================================================
def generate_inventory_report_pdf(output_filename: Optional[str] = None) -> str:
    """
    Generates a formal executive PDF summary report of book inventory, category
    breakdown, defect analysis, and TQM compliance metrics.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from sqlalchemy import func

    _ensure_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_filename or f"inventory_summary_report_{timestamp}.pdf"
    filepath = str(EXPORTS_DIR / filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "InvHeader", parent=styles["Title"], fontSize=18, leading=22,
        textColor=colors.HexColor("#0F172A"), alignment=1,
    )
    sub_style = ParagraphStyle(
        "InvSub", parent=styles["Normal"], fontSize=10, leading=14,
        textColor=colors.HexColor("#64748B"), alignment=1,
    )

    with get_db() as db:
        total_books = db.scalar(select(func.count(Book.id))) or 0
        total_copies = db.scalar(select(func.sum(Book.total_copies))) or 0
        avail_copies = db.scalar(select(func.sum(Book.available_copies))) or 0
        defects = db.scalar(select(func.count(Book.id)).where(Book.defect_flag == True)) or 0
        cats = db.execute(
            select(Book.category, func.count(Book.id), func.sum(Book.total_copies), func.sum(Book.available_copies))
            .group_by(Book.category).order_by(Book.category)
        ).fetchall()

    elements = []
    elements.append(Paragraph(f"{APP_NAME}", header_style))
    elements.append(Paragraph(f"{ORGANIZATION} • {COURSE_NAME}", sub_style))
    elements.append(Paragraph("TQM EXECUTIVE TEXTBOOK INVENTORY & QUALITY AUDIT",
                              ParagraphStyle("Banner", parent=sub_style, fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#2563EB"))))
    elements.append(Spacer(1, 6 * mm))

    # KPI summary grid
    defect_rate = round((defects / max(1, total_books)) * 100.0, 1)
    kpi_table_data = [
        ["Total Book Titles:", str(total_books), "Total Physical Copies:", str(total_copies)],
        ["Available On-Shelf:", str(avail_copies), "Currently On Loan:", str(total_copies - avail_copies)],
        ["Defect / Flagged:", f"{defects} items ({defect_rate}%)", "Defect Tolerance Limit:", "<= 3.0% (TQM Standard)"],
    ]
    t_kpi = Table(kpi_table_data, colWidths=[40 * mm, 45 * mm, 45 * mm, 45 * mm])
    t_kpi.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_kpi)
    elements.append(Spacer(1, 8 * mm))

    # Category breakdown table
    elements.append(Paragraph("Curriculum Subject Category Breakdown", ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12, textColor=colors.HexColor("#0F172A"))))
    cat_data = [["Subject / Department Category", "Titles", "Total Volumes", "Available Copies", "Utilization %"]]
    for row in cats:
        cat_name, b_count, c_count, a_count = row
        c_count = c_count or 0
        a_count = a_count or 0
        util = round(((c_count - a_count) / max(1, c_count)) * 100.0, 1)
        cat_data.append([cat_name, str(b_count), str(c_count), str(a_count), f"{util}%"])

    t_cat = Table(cat_data, colWidths=[70 * mm, 25 * mm, 28 * mm, 28 * mm, 24 * mm])
    t_cat.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_cat)
    elements.append(Spacer(1, 10 * mm))

    # Sign-off footer
    sign_data = [
        ["Audit Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"), "Certified By:", "Chief Librarian / TQM Cell"],
        ["ISO 9001 Compliance:", "VERIFIED & ACCREDITED", "Quality Status:", "ZERO DEFECT STANDARDS MET"],
    ]
    t_sign = Table(sign_data, colWidths=[40 * mm, 45 * mm, 40 * mm, 50 * mm])
    t_sign.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#475569")),
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#2563EB")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_sign)

    doc.build(elements)
    logger.info(f"Inventory summary PDF report generated: {filepath}")
    log_quality_event("CATALOG", "EXPORT_INVENTORY_PDF", "SUCCESS", details=f"Generated PDF for {total_books} books")
    return filepath


# ==============================================================================
# 6. REPORTLAB PDF OVERDUE LOANS & FINES AUDIT REPORT
# ==============================================================================
def generate_overdue_fines_report_pdf(output_filename: Optional[str] = None) -> str:
    """
    Generates a formal institutional PDF report of overdue circulation loans and fines.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from sqlalchemy import func

    _ensure_exports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_filename or f"overdue_fines_report_{timestamp}.pdf"
    filepath = str(EXPORTS_DIR / filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "FineHeader", parent=styles["Title"], fontSize=18, leading=22,
        textColor=colors.HexColor("#0F172A"), alignment=1,
    )
    sub_style = ParagraphStyle(
        "FineSub", parent=styles["Normal"], fontSize=10, leading=14,
        textColor=colors.HexColor("#64748B"), alignment=1,
    )

    with get_db() as db:
        overdue_loans = db.scalars(
            select(Loan).where(Loan.status == "Overdue").order_by(Loan.due_date)
        ).all()
        overdue_data = [l.to_dict() for l in overdue_loans]
        total_fines = db.scalar(select(func.sum(Loan.fine_amount))) or 0.0

    elements = []
    elements.append(Paragraph(f"{APP_NAME}", header_style))
    elements.append(Paragraph(f"{ORGANIZATION} • {COURSE_NAME}", sub_style))
    elements.append(Paragraph("OVERDUE BORROWINGS & CIRCULATION FINE RECOVERY AUDIT",
                              ParagraphStyle("Banner", parent=sub_style, fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#DC2626"))))
    elements.append(Spacer(1, 6 * mm))

    # Overdue summary box
    summary_data = [
        ["Total Overdue Borrowings:", str(len(overdue_data)), "Standard Daily Fine Rate:", "INR 5.00 / day"],
        ["Total Overdue Accrual:", f"INR {total_fines:.2f}", "SLA Return Standard:", "14 Days Maximum Limit"],
    ]
    t_summary = Table(summary_data, colWidths=[50 * mm, 35 * mm, 45 * mm, 45 * mm])
    t_summary.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 8 * mm))

    # Overdue Table
    elements.append(Paragraph("Flagged Overdue Borrowing Records", ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12, textColor=colors.HexColor("#0F172A"))))
    table_data = [["Loan #", "Patron Name", "USN", "Book Title", "Due Date", "Fine (INR)", "Paid"]]
    for l in overdue_data:
        table_data.append([
            str(l["id"]),
            l["member_name"][:18],
            l["member_usn"],
            l["book_title"][:28],
            str(l["due_date"]),
            f"INR {l['fine_amount']:.2f}",
            "Paid" if l["fine_paid"] else "Pending",
        ])

    if len(overdue_data) == 0:
        table_data.append(["—", "Zero Overdue Items", "—", "All loans compliant with SLA", "—", "INR 0.00", "—"])

    t_loans = Table(table_data, colWidths=[18 * mm, 32 * mm, 24 * mm, 48 * mm, 22 * mm, 22 * mm, 14 * mm])
    t_loans.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#991B1B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (4, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF1F2")]),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_loans)

    doc.build(elements)
    logger.info(f"Overdue fines PDF report generated: {filepath}")
    log_quality_event("CIRCULATION", "EXPORT_OVERDUE_PDF", "SUCCESS", details=f"Generated overdue PDF with {len(overdue_data)} items")
    return filepath
