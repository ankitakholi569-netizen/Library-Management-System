"""
app.services — backward-compatible shim layer for legacy test imports.
Wraps the real services in `services.*` with legacy API surface.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import date
import pandas as pd
from sqlalchemy import select, func

from database.db import get_db
from database.models import Loan, Member, Book, QualityLog, User
from services.library_service import (
    get_dashboard_kpis as _real_get_dashboard_kpis,
    issue_book as _real_issue_book,
    return_book as _real_return_book,
    refresh_overdue_statuses,
    log_quality_event,
)
from services.payroll_service import (
    log_shift as _real_log_shift,
    get_staff_shifts as _real_get_staff_shifts,
)
from services.auth_service import authenticate_user
verify_credentials = authenticate_user  # backward-compat alias
from services.report_service import generate_payslip_pdf
from config.settings import TQM_CONFIG

# ---------------------------------------------------------------------------
# Simple alias
# ---------------------------------------------------------------------------
refresh_overdue_status = refresh_overdue_statuses
get_staff_shifts = _real_get_staff_shifts


# ---------------------------------------------------------------------------
# issue_book — legacy tests expect a plain dict return, not a 3-tuple
# ---------------------------------------------------------------------------
def issue_book(book_id: int, member_id: int, processed_by: str = "System") -> dict:
    result = _real_issue_book(book_id, member_id, processed_by=processed_by)
    if isinstance(result, tuple):
        success, data, message = result
        res_dict = {
            "success": success,
            "loan_id": data.get("loan_id") or data.get("id") if data else None,
            "message": message,
            **(data or {}),
        }
        return res_dict
    return result


# ---------------------------------------------------------------------------
# return_book — legacy tests expect a plain dict return, not a 3-tuple
# ---------------------------------------------------------------------------
def return_book(loan_id: Any, processed_by: str = "Librarian", fine_paid: bool = False) -> dict:
    result = _real_return_book(loan_id, processed_by=processed_by, fine_paid=fine_paid)
    if isinstance(result, tuple):
        success, data, message = result
        return {
            "success": success,
            "message": message,
            **(data or {}),
        }
    return result


# ---------------------------------------------------------------------------
# log_shift — legacy tests expect a plain dict return with total_hours
# ---------------------------------------------------------------------------
def log_shift(
    user_id: int,
    shift_date: Optional[date] = None,
    regular_hours: float = 8.0,
    overtime_hours: float = 0.0,
    shift_type: str = "Regular Day Shift",
    tasks_completed: str = "General library circulation and catalog maintenance",
    is_verified: bool = True,
) -> dict:
    result = _real_log_shift(
        user_id=user_id,
        shift_date=shift_date,
        regular_hours=regular_hours,
        overtime_hours=overtime_hours,
        shift_type=shift_type,
        tasks_completed=tasks_completed,
        is_verified=is_verified,
    )
    if isinstance(result, tuple):
        success, data, message = result
        reg = float(regular_hours)
        ot = float(overtime_hours)
        return {
            "success": success,
            "message": message,
            "total_hours": reg + ot,
            "regular_hours": reg,
            "overtime_hours": ot,
            **(data or {}),
        }
    return result


# ---------------------------------------------------------------------------
# Dashboard KPIs — ensure all TQM SLA target keys exist
# ---------------------------------------------------------------------------
def get_dashboard_kpis() -> dict:
    kpis = _real_get_dashboard_kpis()
    sla_target = TQM_CONFIG.get("SLA_TARGET_PERCENT", 90.0)
    defect_tolerance = TQM_CONFIG.get("DEFECT_TOLERANCE_PERCENT", 2.0)
    on_time = kpis.get("on_time_return_rate", 100.0)

    kpis["tqm_sla_target"] = sla_target
    kpis["sla_met"] = "YES" if on_time >= sla_target else "NO"
    kpis["defect_tolerance"] = defect_tolerance
    return kpis


# ---------------------------------------------------------------------------
# Circulation Summary — legacy tests use 'total_loans' & 'total_fines_collected'
# ---------------------------------------------------------------------------
def get_circulation_summary() -> dict:
    with get_db() as db:
        total = db.scalar(select(func.count(Loan.id))) or 0
        fines = db.scalar(
            select(func.sum(Loan.fine_amount)).where(Loan.fine_paid == True)
        ) or 0.0
        active = db.scalar(
            select(func.count(Loan.id)).where(Loan.status.in_(["Borrowed", "issued", "Overdue", "overdue"]))
        ) or 0
        overdue = db.scalar(
            select(func.count(Loan.id)).where(Loan.status.in_(["Overdue", "overdue"]))
        ) or 0
    return {
        "total_loans": total,
        "active_loans": active,
        "overdue_loans": overdue,
        "total_fines_collected": float(fines),
        "total_fines": float(fines),
    }


# ---------------------------------------------------------------------------
# Loans DataFrame
# ---------------------------------------------------------------------------
def get_loans_dataframe() -> pd.DataFrame:
    with get_db() as db:
        loans = db.scalars(select(Loan)).all()
        data = [l.to_dict() for l in loans]
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Department-wise stats — legacy tests call .sort_values("total_loans")
# so must return a DataFrame with that column
# ---------------------------------------------------------------------------
def get_department_wise_stats() -> pd.DataFrame:
    with get_db() as db:
        rows = db.execute(
            select(Member.department, func.count(Loan.id).label("total_loans"))
            .join(Loan, Loan.member_id == Member.id, isouter=True)
            .group_by(Member.department)
        ).all()
    if not rows:
        return pd.DataFrame(columns=["department", "total_loans"])
    return pd.DataFrame([{"department": r[0], "total_loans": r[1]} for r in rows])


# ---------------------------------------------------------------------------
# Quality Log Summary — legacy tests use 'total_entries' & 'avg_execution_ms'
# ---------------------------------------------------------------------------
def get_quality_log_summary() -> dict:
    with get_db() as db:
        total = db.scalar(select(func.count(QualityLog.id))) or 0
        defects = db.scalar(
            select(func.count(QualityLog.id)).where(QualityLog.status == "DEFECT")
        ) or 0
        avg_lat = db.scalar(select(func.avg(QualityLog.execution_time_ms))) or 0.0
    return {
        "total_entries": total,
        "total_events": total,
        "defect_count": defects,
        "avg_execution_ms": round(float(avg_lat), 2),
        "avg_latency_ms": round(float(avg_lat), 2),
    }
