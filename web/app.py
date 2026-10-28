"""
Flask Localhost Web Application for Library Management System (TQM Edition).
Course: BBAT104 - Total Quality Management.

Shares the exact same SQLite database, SQLAlchemy models, and service layer
with the PySide6 Desktop application with zero code duplication.
"""

from __future__ import annotations

import os
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
        limit = int(request.args.get("limit", 10))
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
            if not title or not author or not isbn:
                return jsonify({"success": False, "error": "Title, Author, and ISBN are required."}), 400

            ok, book_dict, msg = add_book(
                title=title,
                author=author,
                isbn=isbn,
                category=data.get("category", "General"),
                year=int(data.get("year", date.today().year)),
                total_copies=int(data.get("total_copies", 1)),
                shelf_location=data.get("shelf_location", "Aisle 1 - Rack A"),
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
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))

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
            if not usn or not name:
                return jsonify({"success": False, "error": "USN and Name are required."}), 400

            ok, member_dict, msg = add_member(
                usn=usn,
                name=name,
                department=data.get("department", "CSE"),
                semester=int(data.get("semester", 1)),
                membership_type=data.get("membership_type", "Student"),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                processed_by=data.get("processed_by", "Web Portal User"),
            )
            if not ok:
                return jsonify({"success": False, "error": msg}), 400
            return jsonify({"success": True, "member": member_dict, "message": msg}), 201

        query = request.args.get("q", "").strip()
        department = request.args.get("department", "").strip()
        membership_type = request.args.get("membership_type", "").strip()
        status = request.args.get("status", "").strip()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))

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
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))

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
            return jsonify({"success": False, "error": "book_id and member_id are required."}), 400

        loan_days = int(data.get("loan_days", 14))
        processed_by = data.get("processed_by", "Web Circulation Desk")

        ok, loan_dict, msg = issue_book(
            book_id=int(book_id),
            member_id=int(member_id),
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
                return jsonify({"success": False, "error": "user_id is required"}), 400

            shift_date_str = data.get("shift_date")
            target_date = datetime.strptime(shift_date_str, "%Y-%m-%d").date() if shift_date_str else date.today()

            ok, shift_dict, msg = log_shift(
                user_id=int(user_id),
                shift_date=target_date,
                regular_hours=float(data.get("regular_hours", 8.0)),
                overtime_hours=float(data.get("overtime_hours", 0.0)),
                shift_type=data.get("shift_type", "Regular Day Shift"),
                tasks_completed=data.get("tasks_completed", "Standard desk duty"),
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
            month = int(data.get("month", date.today().month))
            year = int(data.get("year", date.today().year))

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
