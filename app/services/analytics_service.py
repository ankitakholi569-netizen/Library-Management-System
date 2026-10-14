"""
Analytics Service — Pandas TQM Statistical Metrics & KPI Aggregations.
Demonstrates TQM Principle: Data-Driven Decision Making & Continuous Improvement.
"""

from datetime import date, timedelta
from sqlalchemy import select, func
import pandas as pd
from app.models.base import get_db
from app.models.book import Book
from app.models.member import Member
from app.models.loan import Loan
from app.models.user import User
from app.models.payroll import StaffShift, StaffPayroll
from app.models.quality_log import QualityLog
from app.config import TQM_CONFIG
from app.core.logger import get_logger

logger = get_logger("analytics")


def get_dashboard_kpis() -> dict:
    """
    Computes real-time KPIs for the executive dashboard.
    Returns key metrics: total books, members, active loans, overdue rate, on-time return rate.
    """
    with get_db() as db:
        total_books = db.scalar(select(func.count(Book.id))) or 0
        total_members = db.scalar(select(func.count(Member.id))) or 0
        total_loans = db.scalar(select(func.count(Loan.id))) or 0
        active_loans = db.scalar(
            select(func.count(Loan.id)).where(Loan.status.in_(["Borrowed", "Overdue"]))
        ) or 0
        overdue_loans = db.scalar(
            select(func.count(Loan.id)).where(Loan.status == "Overdue")
        ) or 0
        returned_loans = db.scalar(
            select(func.count(Loan.id)).where(Loan.status == "Returned")
        ) or 0
        total_staff = db.scalar(select(func.count(User.id))) or 0

        # TQM SLA Metric: On-Time Return Rate
        on_time_returns = db.scalar(
            select(func.count(Loan.id)).where(
                Loan.status == "Returned",
                Loan.fine_amount == 0,
            )
        ) or 0
        on_time_rate = round((on_time_returns / returned_loans * 100), 1) if returned_loans > 0 else 100.0

        # Defect Rate (books flagged with defects)
        defective_books = db.scalar(
            select(func.count(Book.id)).where(Book.defect_flag == True)
        ) or 0
        defect_rate = round((defective_books / total_books * 100), 2) if total_books > 0 else 0.0

        # Total fines
        total_fines = db.scalar(
            select(func.sum(Loan.fine_amount)).where(Loan.fine_amount > 0)
        ) or 0.0

        return {
            "total_books": total_books,
            "total_members": total_members,
            "total_staff": total_staff,
            "total_loans": total_loans,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "returned_loans": returned_loans,
            "on_time_return_rate": on_time_rate,
            "tqm_sla_target": TQM_CONFIG["TARGET_ON_TIME_RETURN_RATE"],
            "sla_met": on_time_rate >= TQM_CONFIG["TARGET_ON_TIME_RETURN_RATE"],
            "defect_rate": defect_rate,
            "defect_tolerance": TQM_CONFIG["DEFECT_TOLERANCE_RATE"],
            "total_fines": round(total_fines, 2),
        }


def get_loans_dataframe() -> pd.DataFrame:
    """Converts loan data to a Pandas DataFrame for analysis and charting."""
    with get_db() as db:
        loans = db.scalars(select(Loan)).all()
        records = []
        for loan in loans:
            records.append({
                "loan_id": loan.id,
                "book_title": loan.book.title if loan.book else "N/A",
                "member_name": loan.member.name if loan.member else "N/A",
                "department": loan.member.department if loan.member else "N/A",
                "issue_date": loan.issue_date,
                "due_date": loan.due_date,
                "return_date": loan.return_date,
                "status": loan.status,
                "fine_amount": loan.fine_amount,
                "overdue_days": loan.days_overdue(),
            })
        return pd.DataFrame(records)


def get_department_wise_stats() -> pd.DataFrame:
    """Generates department-wise borrowing statistics using Pandas groupby."""
    df = get_loans_dataframe()
    if df.empty:
        return pd.DataFrame()

    stats = df.groupby("department").agg(
        total_loans=("loan_id", "count"),
        overdue_count=("status", lambda x: (x == "Overdue").sum()),
        total_fines=("fine_amount", "sum"),
    ).reset_index()
    stats["overdue_percentage"] = round(stats["overdue_count"] / stats["total_loans"] * 100, 1)
    return stats


def get_book_popularity() -> pd.DataFrame:
    """Returns top borrowed books ranked by loan frequency."""
    df = get_loans_dataframe()
    if df.empty:
        return pd.DataFrame()

    popularity = df.groupby("book_title").agg(
        times_borrowed=("loan_id", "count"),
        total_fines=("fine_amount", "sum"),
    ).sort_values("times_borrowed", ascending=False).reset_index()
    return popularity


def get_monthly_trends() -> pd.DataFrame:
    """Generates monthly loan trend data for time-series charting."""
    df = get_loans_dataframe()
    if df.empty:
        return pd.DataFrame()

    df["month"] = pd.to_datetime(df["issue_date"]).dt.to_period("M")
    trends = df.groupby("month").agg(
        loans_issued=("loan_id", "count"),
        fines_collected=("fine_amount", "sum"),
    ).reset_index()
    trends["month"] = trends["month"].astype(str)
    return trends


def get_quality_log_summary() -> dict:
    """Summarizes quality log entries by module and status."""
    with get_db() as db:
        logs = db.scalars(select(QualityLog)).all()
        records = [{
            "module": log.module,
            "action": log.action,
            "status": log.status,
            "execution_time_ms": log.execution_time_ms,
        } for log in logs]

        df = pd.DataFrame(records)
        if df.empty:
            return {"total_entries": 0, "by_module": {}, "by_status": {}}

        return {
            "total_entries": len(df),
            "by_module": df["module"].value_counts().to_dict(),
            "by_status": df["status"].value_counts().to_dict(),
            "avg_execution_ms": round(df["execution_time_ms"].mean(), 2),
        }
