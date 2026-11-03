"""
Flask Localhost Web Application for Library Management System (TQM Edition).
Course: BBAT104 - Total Quality Management.

Shares the exact same SQLite database, SQLAlchemy models, and service layer
with the PySide6 Desktop application with zero code duplication.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request, send_file, render_template

from config.settings import APP_NAME, COURSE_NAME, APP_VERSION
from database.db import get_db
from database.models import Book, Member, Loan, StaffShift, StaffPayroll, QualityLog, User
from database.seed import seed_database
from services.auth_service import get_all_users, get_staff_users, authenticate_user
from services.library_service import (
    fast_pos_issue,
    inward_grn_entry,
    get_fefo_stock_ledger,
    verify_stock_balance,
    generate_daily_z_report,
    get_21cfr_audit_trail,
    get_all_books,
    get_book_by_id,
    get_book_categories,
    add_book,
    update_book,
    delete_book,
    get_all_members,
    get_member_by_id,
    get_member_departments,
    add_member,
    update_member,
    delete_member,
    get_member_loan_history,
    issue_book,
    return_book,
    mark_fine_paid,
    get_all_loans,
    refresh_overdue_statuses,
    get_dashboard_kpis,
)
from services.search_service import (
    student_kiosk_search,
    faculty_research_search,
    quick_search,
    search_books,
    search_members,
    search_loans,
    get_search_kpi_summary,
)
from services.payroll_service import (
    log_shift,
    get_staff_shifts,
    generate_monthly_payroll,
    generate_all_staff_payrolls,
    get_all_payrolls,
    get_payroll_by_id,
    update_payroll_status,
)
from services.report_service import (
    generate_payslip_pdf,
    generate_catalog_excel,
    generate_quality_audit_excel,
)
from services.logger_service import get_logger, timed_operation

logger = get_logger("web_app")


def create_app() -> Flask:
    """Application factory for the Flask Web Portal."""
    template_dir = Path(__file__).resolve().parent / "templates"
    static_dir = Path(__file__).resolve().parent / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir)
    )
    app.config["JSON_SORT_KEYS"] = False
    app.config["SECRET_KEY"] = "tqm-web-app-secret-key-bbat104"

    # Ensure DB is ready on startup
    seed_database()

    # =========================================================================
    # 1. HTML WEB DASHBOARD
    # =========================================================================
    @app.route("/")
    def index():
        return render_template(
            "index.html",
            app_name=APP_NAME,
            course_name=COURSE_NAME,
            version=APP_VERSION,
        )

    # =========================================================================
    # 2. REST API: TQM DASHBOARD KPIS & ANALYTICS
    # =========================================================================
    @app.route("/api/kpis", methods=["GET"])
    def api_kpis():
        with timed_operation("WEB_API", "GET_KPIS"):
            kpis = get_dashboard_kpis()
            search_summary = get_search_kpi_summary()
            with get_db() as db:
                from sqlalchemy import select, func
                total_shifts = db.scalar(select(func.count(StaffShift.id))) or 0
                total_payrolls = db.scalar(select(func.count(StaffPayroll.id))) or 0

            return jsonify({
                "success": True,
                "kpis": {
                    "total_books": kpis.get("total_books", 0),
                    "defect_books": kpis.get("defect_books", 0),
                    "total_members": kpis.get("total_members", 0),
                    "active_loans": kpis.get("active_loans", 0),
                    "overdue_loans": kpis.get("overdue_loans", 0),
                    "on_time_return_rate": kpis.get("on_time_rate", 100.0),
                    "defect_rate": kpis.get("defect_rate", 0.0),
                    "total_shifts": total_shifts,
                    "total_payrolls": total_payrolls,
                    "search_avg_latency_ms": search_summary.get("avg_latency_ms", 3.5),
                    "search_sla_pass_rate": search_summary.get("sla_pass_rate", 100.0),
                }
            })

    # =========================================================================
    # 3. REST API: QUALITY GOAL 1 — FASTER SEARCH & RETRIEVAL
    # =========================================================================
    @app.route("/api/search/quick", methods=["GET"])
    def api_quick_search():
        query = request.args.get("q", "").strip()
        try:
            limit = int(request.args.get("limit", 10))
        except (ValueError, TypeError):
            limit = 10
        result = quick_search(query=query, limit=limit)
        return jsonify({
            "success": True,
            "matched_books": result["books"],
            "matched_members": result["members"],
            **result
        })

    @app.route("/api/search/kpi", methods=["GET"])
    def api_search_kpis():
        summary = get_search_kpi_summary()
        return jsonify({"success": True, "kpi_summary": summary})

    # =========================================================================
    # 4. REST API: BOOK CATALOG & CRUD
    # =========================================================================
    @app.route("/api/categories", methods=["GET"])
    def api_categories():
        cats = get_book_categories()
        return jsonify({"success": True, "categories": cats})

    @app.route("/api/books", methods=["GET", "POST"])
    def api_books():
        if request.method == "POST":
            data = request.get_json() or {}
            title = data.get("title", "").strip()
            author = data.get("author", "").strip()
            isbn = data.get("isbn", "").strip()
            category = data.get("category", "General").strip() or "General"
            shelf_location = data.get("shelf_location", "Aisle 1 - Rack A").strip() or "Aisle 1 - Rack A"

            if not title:
                return jsonify({"success": False, "error": "Book title is required."}), 400
            if len(title) < 2:
                return jsonify({"success": False, "error": "Book title must be at least 2 characters long."}), 400

            if not author:
                return jsonify({"success": False, "error": "Author name is required."}), 400
            if len(author) < 2:
                return jsonify({"success": False, "error": "Author name must be at least 2 characters long."}), 400

            if not isbn:
                return jsonify({"success": False, "error": "ISBN is required."}), 400
            if len(isbn) < 5:
                return jsonify({"success": False, "error": "Valid ISBN is required (minimum 5 characters)."}), 400

            try:
                year_val = int(data.get("year", date.today().year))
                if year_val < 1000 or year_val > 2100:
                    return jsonify({"success": False, "error": "Publication year must be between 1000 and 2100."}), 400
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Publication year must be a valid number."}), 400

            try:
                copies_val = int(data.get("total_copies", 1))
                if copies_val < 1:
                    return jsonify({"success": False, "error": "Total copies must be at least 1."}), 400
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Total copies must be a valid number."}), 400

            ok, book_dict, msg = add_book(
                title=title,
                author=author,
                isbn=isbn,
                category=category,
                year=year_val,
                total_copies=copies_val,
                shelf_location=shelf_location,
                processed_by=data.get("processed_by", "Web Portal User"),
            )
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            if data.get("defect_flag") or data.get("defect_notes"):
                update_book(
                    book_dict["id"],
                    defect_flag=bool(data.get("defect_flag")),
                    defect_notes=data.get("defect_notes", ""),
                    processed_by="Web Inspection",
                )
            return jsonify({"success": True, "book": book_dict, "message": msg}), 201

        # GET books with search, filter, and pagination
        query = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        availability = request.args.get("availability", "").strip()
        sort_by = request.args.get("sort_by", "id")
        sort_dir = request.args.get("sort_dir", "desc")
        try:
            page = int(request.args.get("page", 1))
            page_size = int(request.args.get("page_size", 50))
        except (ValueError, TypeError):
            page = 1
            page_size = 50

        result = search_books(
            query=query,
            category=category,
            availability=availability,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        return jsonify({
            "success": True,
            "count": len(result["results"]),
            "total": result["total"],
            "page": result.get("page", 1),
            "pages": result.get("pages", 1),
            "total_pages": result.get("pages", 1),
            "latency_ms": result["latency_ms"],
            "sla_ok": result["sla_ok"],
            "books": result["results"],
        })

    @app.route("/api/books/<int:book_id>", methods=["GET", "PUT", "DELETE"])
    def api_book_detail(book_id: int):
        if request.method == "GET":
            book = get_book_by_id(book_id)
            if not book:
                return jsonify({"success": False, "error": f"Book {book_id} not found"}), 404
            return jsonify({"success": True, "book": book})

        if request.method == "PUT":
            data = request.get_json() or {}
            kwargs: Dict[str, Any] = {}
            for field in ["title", "author", "isbn", "category", "year", "total_copies",
                          "shelf_location", "defect_flag", "defect_notes"]:
                if field in data:
                    kwargs[field] = data[field]
            kwargs["processed_by"] = data.get("processed_by", "Web Portal User")

            ok, book_dict, msg = update_book(book_id, **kwargs)
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            return jsonify({"success": True, "book": book_dict, "message": msg})

        if request.method == "DELETE":
            processed_by = request.args.get("processed_by", "Web Portal User")
            ok, msg = delete_book(book_id, processed_by=processed_by)
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            return jsonify({"success": True, "message": msg})

    @app.route("/api/books/<int:book_id>/toggle-defect", methods=["POST"])
    def api_book_toggle_defect(book_id: int):
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({"success": False, "error": "Book not found"}), 404
        new_status = not book["defect_flag"]
        ok, book_dict, msg = update_book(book_id, defect_flag=new_status, processed_by="Web Quality Audit")
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "book": book_dict, "message": f"Defect status set to {new_status}"})

    # =========================================================================
    # 5. REST API: MEMBERS DIRECTORY & CRUD
    # =========================================================================
    @app.route("/api/departments", methods=["GET"])
    def api_departments():
        depts = get_member_departments()
        return jsonify({"success": True, "departments": depts})

    @app.route("/api/members", methods=["GET", "POST"])
    def api_members():
        if request.method == "POST":
            data = request.get_json() or {}
            usn = data.get("usn", "").strip().upper()
            name = data.get("name", "").strip()
            department = data.get("department", "CSE").strip() or "CSE"
            membership_type = data.get("membership_type", "Student").strip() or "Student"
            email = data.get("email", "").strip()
            phone = data.get("phone", "").strip()

            if not usn:
                return jsonify({"success": False, "error": "USN / Member ID is required."}), 400
            if len(usn) < 3:
                return jsonify({"success": False, "error": "USN must be at least 3 characters long."}), 400

            if not name:
                return jsonify({"success": False, "error": "Member name is required."}), 400
            if len(name) < 2:
                return jsonify({"success": False, "error": "Member name must be at least 2 characters long."}), 400

            if not department:
                return jsonify({"success": False, "error": "Department is required."}), 400

            try:
                sem_val = int(data.get("semester", 1))
                if sem_val < 0 or sem_val > 12:
                    return jsonify({"success": False, "error": "Semester must be between 0 and 12."}), 400
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Semester must be a valid integer."}), 400

            if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                return jsonify({"success": False, "error": f"Invalid email format: '{email}'."}), 400

            if phone and not re.match(r"^\d{10}$", phone):
                return jsonify({"success": False, "error": "Phone number must be a valid 10-digit number (not more or less than 10 digits)."}), 400

            ok, member_dict, msg = add_member(
                usn=usn,
                name=name,
                department=department,
                semester=sem_val,
                membership_type=membership_type,
                email=email,
                phone=phone,
                processed_by=data.get("processed_by", "Web Portal User"),
            )
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            return jsonify({"success": True, "member": member_dict, "message": msg}), 201

        query = request.args.get("q", "").strip()
        department = request.args.get("department", "").strip()
        membership_type = request.args.get("membership_type", "").strip()
        status = request.args.get("status", "").strip()
        try:
            page = int(request.args.get("page", 1))
            page_size = int(request.args.get("page_size", 50))
        except (ValueError, TypeError):
            page = 1
            page_size = 50

        result = search_members(
            query=query,
            department=department,
            membership_type=membership_type,
            status=status,
            page=page,
            page_size=page_size,
        )
        return jsonify({
            "success": True,
            "count": len(result["results"]),
            "total": result["total"],
            "page": result.get("page", 1),
            "pages": result.get("pages", 1),
            "total_pages": result.get("pages", 1),
            "latency_ms": result["latency_ms"],
            "sla_ok": result["sla_ok"],
            "members": result["results"],
        })

    @app.route("/api/members/<int:member_id>", methods=["GET", "PUT", "DELETE"])
    def api_member_detail(member_id: int):
        if request.method == "GET":
            member = get_member_by_id(member_id)
            if not member:
                return jsonify({"success": False, "error": f"Member {member_id} not found"}), 404
            return jsonify({"success": True, "member": member})

        if request.method == "PUT":
            data = request.get_json() or {}
            kwargs: Dict[str, Any] = {}
            for field in ["name", "department", "semester", "membership_type", "email", "phone", "status"]:
                if field in data:
                    kwargs[field] = data[field]
            kwargs["processed_by"] = data.get("processed_by", "Web Portal User")

            ok, member_dict, msg = update_member(member_id, **kwargs)
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            return jsonify({"success": True, "member": member_dict, "message": msg})

        if request.method == "DELETE":
            processed_by = request.args.get("processed_by", "Web Portal User")
            ok, msg = delete_member(member_id, processed_by=processed_by)
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            return jsonify({"success": True, "message": msg})

    @app.route("/api/members/<int:member_id>/loans", methods=["GET"])
    def api_member_loans(member_id: int):
        loans = get_member_loan_history(member_id)
        return jsonify({"success": True, "count": len(loans), "loans": loans})

    @app.route("/api/members/<int:member_id>/toggle-status", methods=["POST"])
    def api_member_toggle_status(member_id: int):
        member = get_member_by_id(member_id)
        if not member:
            return jsonify({"success": False, "error": "Member not found"}), 404
        new_status = "Suspended" if member["status"] == "Active" else "Active"
        ok, member_dict, msg = update_member(member_id, status=new_status, processed_by="Web Desk")
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "member": member_dict, "message": f"Member status set to {new_status}"})

    # =========================================================================
    # 6. REST API: CIRCULATION DESK (ISSUE, RETURN & SLA FINES)
    # =========================================================================
    @app.route("/api/loans", methods=["GET"])
    def api_loans():
        query = request.args.get("q", "").strip()
        status = request.args.get("status", "").strip()
        try:
            page = int(request.args.get("page", 1))
            page_size = int(request.args.get("page_size", 50))
        except (ValueError, TypeError):
            page = 1
            page_size = 50

        result = search_loans(
            query=query,
            status=status,
            page=page,
            page_size=page_size,
        )
        return jsonify({
            "success": True,
            "count": len(result["results"]),
            "total": result["total"],
            "page": result.get("page", 1),
            "pages": result.get("pages", 1),
            "total_pages": result.get("pages", 1),
            "latency_ms": result["latency_ms"],
            "sla_ok": result["sla_ok"],
            "loans": result["results"],
        })

    @app.route("/api/loans/issue", methods=["POST"])
    def api_issue_book():
        data = request.get_json() or {}
        book_id = data.get("book_id")
        member_id = data.get("member_id")
        if not book_id or not member_id:
            return jsonify({"success": False, "error": "Both Book and Member selection are required."}), 400

        try:
            b_id = int(book_id)
            m_id = int(member_id)
            if b_id <= 0 or m_id <= 0:
                return jsonify({"success": False, "error": "Valid Book and Member IDs are required."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid Book or Member ID format."}), 400

        try:
            loan_days = int(data.get("loan_days", 14))
            if loan_days <= 0:
                return jsonify({"success": False, "error": "Loan period must be at least 1 day."}), 400
        except (ValueError, TypeError):
            loan_days = 14

        processed_by = data.get("processed_by", "Web Circulation Desk")

        ok, loan_dict, msg = issue_book(
            book_id=b_id,
            member_id=m_id,
            loan_days=loan_days,
            processed_by=processed_by,
        )
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "loan": loan_dict, "message": msg}), 201

    @app.route("/api/loans/<int:loan_id>/return", methods=["POST"])
    def api_return_book(loan_id: int):
        data = request.get_json() or {}
        processed_by = data.get("processed_by", "Web Circulation Desk")
        fine_paid = bool(data.get("fine_paid", False))

        ok, loan_dict, msg = return_book(
            loan_id=loan_id,
            processed_by=processed_by,
            fine_paid=fine_paid,
        )
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "loan": loan_dict, "message": msg})

    @app.route("/api/loans/<int:loan_id>/pay-fine", methods=["POST"])
    def api_pay_fine(loan_id: int):
        data = request.get_json() or {}
        processed_by = data.get("processed_by", "Web Circulation Desk")
        ok, loan_dict, msg = mark_fine_paid(loan_id, processed_by=processed_by)
        if not ok:
            return jsonify({"success": False, "error": msg}), 400
        return jsonify({"success": True, "loan": loan_dict, "message": msg})

    @app.route("/api/loans/refresh-overdue", methods=["POST"])
    def api_refresh_overdue():
        count = refresh_overdue_statuses()
        return jsonify({
            "success": True,
            "message": f"Overdue SLA refresh completed. {count} loans updated.",
            "updated_count": count,
        })

    # =========================================================================
    # 7. REST API: STAFF & SHIFT ATTENDANCE
    # =========================================================================
    @app.route("/api/staff", methods=["GET"])
    def api_staff():
        users = get_staff_users()
        return jsonify({"success": True, "count": len(users), "staff": users})

    @app.route("/api/shifts", methods=["GET", "POST"])
    def api_shifts():
        if request.method == "POST":
            data = request.get_json() or {}
            user_id = data.get("user_id")
            if not user_id:
                return jsonify({"success": False, "error": "Staff member (user_id) is required."}), 400

            try:
                u_id = int(user_id)
                if u_id <= 0:
                    return jsonify({"success": False, "error": "Valid staff user ID is required."}), 400
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Invalid staff user ID format."}), 400

            try:
                reg_h = float(data.get("regular_hours", 8.0))
                ot_h = float(data.get("overtime_hours", 0.0))
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Working hours must be numbers."}), 400

            if reg_h < 0 or ot_h < 0:
                return jsonify({"success": False, "error": "Working hours cannot be negative."}), 400
            if reg_h + ot_h <= 0:
                return jsonify({"success": False, "error": "Total shift hours (regular + overtime) must be greater than zero."}), 400
            if reg_h + ot_h > 24.0:
                return jsonify({"success": False, "error": "Total shift hours cannot exceed 24 hours in a single day."}), 400

            tasks = data.get("tasks_completed", "").strip()
            if not tasks:
                return jsonify({"success": False, "error": "Task summary description is required."}), 400

            shift_date_str = data.get("shift_date")
            target_date = datetime.strptime(shift_date_str, "%Y-%m-%d").date() if shift_date_str else date.today()

            ok, shift_dict, msg = log_shift(
                user_id=u_id,
                shift_date=target_date,
                regular_hours=reg_h,
                overtime_hours=ot_h,
                shift_type=data.get("shift_type", "Regular Day Shift").strip() or "Regular Day Shift",
                tasks_completed=tasks,
                is_verified=bool(data.get("is_verified", True)),
            )
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            return jsonify({"success": True, "shift": shift_dict, "message": msg}), 201

        shifts = get_staff_shifts()
        return jsonify({"success": True, "count": len(shifts), "shifts": shifts})

    # =========================================================================
    # 8. REST API: AUTOMATED PAYROLL PROCESSING
    # =========================================================================
    @app.route("/api/payrolls", methods=["GET", "POST"])
    def api_payrolls():
        if request.method == "POST":
            data = request.get_json() or {}
            try:
                month = int(data.get("month", date.today().month))
                year = int(data.get("year", date.today().year))
                if not (1 <= month <= 12):
                    return jsonify({"success": False, "error": "Month must be between 1 and 12."}), 400
                if year < 2000 or year > 2099:
                    return jsonify({"success": False, "error": "Year must be between 2000 and 2099."}), 400
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Month and Year must be valid integers."}), 400

            count, records = generate_all_staff_payrolls(month, year)
            return jsonify({
                "success": True,
                "message": f"Automated payroll processed for {count} staff accounts.",
                "period": f"{month:02d}/{year}",
                "records": records,
            }), 201

        payrolls = get_all_payrolls()
        return jsonify({"success": True, "count": len(payrolls), "payrolls": payrolls})

    # =========================================================================
    # 9. REST API: TQM QUALITY AUDIT LOGS
    # =========================================================================
    @app.route("/api/quality-logs", methods=["GET"])
    def api_quality_logs():
        with get_db() as db:
            from sqlalchemy import select
            logs = db.scalars(select(QualityLog).order_by(QualityLog.timestamp.desc()).limit(100)).all()
            return jsonify({
                "success": True,
                "count": len(logs),
                "logs": [l.to_dict() for l in logs]
            })

    # =========================================================================
    # 10. FILE DOWNLOAD EXPORT ROUTES (PDF & EXCEL)
    # =========================================================================
    @app.route("/export/payslip/<int:payroll_id>")
    def export_payslip(payroll_id: int):
        payroll = get_payroll_by_id(payroll_id)
        if not payroll:
            return jsonify({"success": False, "error": "Payroll record not found"}), 404

        pdf_path = generate_payslip_pdf(
            staff_name=payroll["staff_name"],
            period=payroll["period"],
            gross=payroll["gross_salary"],
            deductions=payroll["deductions"],
            net=payroll["net_salary"],
            regular_hours=payroll["total_regular_hours"],
            overtime_hours=payroll["total_overtime_hours"],
            hourly_rate=payroll["hourly_rate"],
            role=payroll["role"],
        )
        return send_file(pdf_path, as_attachment=True)

    @app.route("/export/catalog")
    def export_catalog():
        cat = request.args.get("category")
        excel_path = generate_catalog_excel(category=cat)
        return send_file(excel_path, as_attachment=True)

    @app.route("/export/quality-audit")
    def export_quality_audit():
        excel_path = generate_quality_audit_excel()
        return send_file(excel_path, as_attachment=True)


    # =========================================================================
    # 11. SRS STAKEHOLDER SPECIFIC REST APIS (FR-01 to FR-05)
    # =========================================================================

    # FR-01: Student Kiosk Search (30 req/min rate limit, sub-85ms search)
    @app.route("/api/kiosk/search", methods=["GET"])
    def api_kiosk_search():
        q = request.args.get("q", "")
        client_ip = request.remote_addr or "kiosk_client"
        res = student_kiosk_search(query=q, client_id=client_ip)
        status_code = 429 if not res.get("success") and res.get("rate_limit_breach") else 200
        return jsonify(res), status_code

    # FR-02: Faculty Research Search (120 req/min, citation sort, multi-filter)
    @app.route("/api/faculty/search", methods=["GET"])
    def api_faculty_search():
        q = request.args.get("q", "")
        cat = request.args.get("category")
        min_year = request.args.get("min_year", type=int)
        max_year = request.args.get("max_year", type=int)
        peer_reviewed = request.args.get("peer_reviewed", "").lower() in ("true", "1", "yes")
        sort_by = request.args.get("sort_by", "citations")
        client_ip = request.remote_addr or "faculty_client"

        res = faculty_research_search(
            query=q,
            category=cat,
            min_year=min_year,
            max_year=max_year,
            peer_reviewed_only=peer_reviewed,
            sort_by=sort_by,
            client_id=client_ip
        )
        status_code = 429 if not res.get("success") and res.get("rate_limit_breach") else 200
        return jsonify(res), status_code

    # FR-03: POS Circulation Bay 1-Click Issue (Sub-1s loan completion)
    @app.route("/api/pos/issue", methods=["POST"])
    def api_pos_issue():
        data = request.get_json() or {}
        isbn = data.get("isbn") or data.get("barcode")
        usn = data.get("usn")
        operator = data.get("processed_by", "Circulation Staff")
        res = fast_pos_issue(isbn_or_barcode=isbn, usn=usn, processed_by=operator)
        status_code = 200 if res.get("success") else 400
        return jsonify(res), status_code

    # FR-04: FEFO Stock Ledger & Inward GRN Entry (100% Stock Balance)
    @app.route("/api/grn/inward", methods=["POST"])
    def api_grn_inward():
        data = request.get_json() or {}
        supplier = data.get("supplier_name")
        grn_no = data.get("grn_number")
        inv_no = data.get("invoice_no", "")
        book_id = data.get("book_id")
        qty = int(data.get("quantity", 1))
        unit_cost = float(data.get("unit_cost", 0.0))
        created_by = data.get("created_by", "Catalog Manager")

        res = inward_grn_entry(
            supplier_name=supplier,
            grn_number=grn_no,
            invoice_no=inv_no,
            book_id=book_id,
            quantity=qty,
            unit_cost=unit_cost,
            created_by=created_by,
        )
        status_code = 200 if res.get("success") else 400
        return jsonify(res), status_code

    @app.route("/api/grn/ledger", methods=["GET"])
    def api_grn_ledger():
        entries = get_fefo_stock_ledger()
        return jsonify({"success": True, "count": len(entries), "ledger": entries})

    @app.route("/api/grn/verify-balance", methods=["GET"])
    def api_grn_verify_balance():
        bal = verify_stock_balance()
        return jsonify({"success": True, **bal})

    # FR-05: Daily Z-Report Till Close (Zero Audit Variance)
    @app.route("/api/admin/z-report", methods=["GET", "POST"])
    def api_admin_z_report():
        operator = request.args.get("operator", "Library Admin")
        res = generate_daily_z_report(report_date=date.today(), generated_by=operator)
        return jsonify(res)

    @app.route("/api/admin/audit-21cfr", methods=["GET"])
    def api_admin_audit_21cfr():
        logs = get_21cfr_audit_trail(limit=100)
        return jsonify({"success": True, "count": len(logs), "audit_logs": logs})

    return app


# Create default instance for running with `flask run` or `waitress`
app = create_app()

if __name__ == "__main__":
    try:
        from waitress import serve
        print(f"Starting {APP_NAME} Production WSGI Server on http://127.0.0.1:5000 ...")
        serve(app, host="127.0.0.1", port=5000, threads=6)
    except ImportError:
        print(f"Starting {APP_NAME} Web Server on http://127.0.0.1:5000 ...")
        app.run(host="127.0.0.1", port=5000, debug=False)
