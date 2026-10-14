"""
Payroll Service — Shift Aggregation & Automated Salary Calculation.
Demonstrates TQM Principle: Error Reduction & Standardized Calculation.
"""

from datetime import date
from sqlalchemy import select, func
from app.models.base import get_db
from app.models.user import User
from app.models.payroll import StaffShift, StaffPayroll
from app.models.quality_log import QualityLog
from app.config import TQM_CONFIG
from app.core.logger import get_logger
import time

logger = get_logger("payroll")


def log_shift(user_id: int, shift_date: date = None, regular_hours: float = 8.0,
              overtime_hours: float = 0.0, tasks_completed: str = "",
              shift_type: str = "Regular Day Shift") -> dict:
    """Records a staff shift entry for a given user."""
    start = time.time()
    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return {"success": False, "message": f"User ID {user_id} not found."}

        shift = StaffShift(
            user_id=user_id,
            shift_date=shift_date or date.today(),
            shift_type=shift_type,
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            tasks_completed=tasks_completed or "General library operations",
            is_verified=True,
        )
        db.add(shift)
        db.flush()

        elapsed = round((time.time() - start) * 1000, 2)
        db.add(QualityLog(
            module="PAYROLL",
            action="SHIFT_LOGGED",
            status="SUCCESS",
            execution_time_ms=elapsed,
            details=f"Shift logged for '{user.full_name}': {regular_hours}h + {overtime_hours}h OT on {shift.shift_date}",
        ))

        logger.info(f"Shift logged for {user.full_name}: {regular_hours}h + {overtime_hours}h OT")
        return {
            "success": True,
            "message": f"Shift recorded for {user.full_name}.",
            "shift_id": shift.id,
            "total_hours": shift.total_hours(),
        }


def generate_payroll(user_id: int, month: int = None, year: int = None) -> dict:
    """
    Aggregates verified shifts and generates automated payroll for a staff member.
    Demonstrates TQM Process Automation & Error Reduction.
    """
    start = time.time()
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return {"success": False, "message": f"User ID {user_id} not found."}

        # Check for existing payroll for this period
        existing = db.scalar(
            select(StaffPayroll).where(
                StaffPayroll.user_id == user_id,
                StaffPayroll.period_month == target_month,
                StaffPayroll.period_year == target_year,
            )
        )
        if existing:
            return {
                "success": False,
                "message": f"Payroll already exists for {user.full_name} ({target_month}/{target_year}). Net: Rs. {existing.net_salary}",
            }

        # Aggregate verified shifts for the period
        shifts = db.scalars(
            select(StaffShift).where(
                StaffShift.user_id == user_id,
                StaffShift.is_verified == True,
                func.extract("month", StaffShift.shift_date) == target_month,
                func.extract("year", StaffShift.shift_date) == target_year,
            )
        ).all()

        total_regular = sum(s.regular_hours for s in shifts)
        total_overtime = sum(s.overtime_hours for s in shifts)

        payroll = StaffPayroll(
            user_id=user_id,
            period_month=target_month,
            period_year=target_year,
            total_regular_hours=total_regular,
            total_overtime_hours=total_overtime,
            hourly_rate=TQM_CONFIG["HOURLY_PAY_RATE"],
            status="Processed",
        )
        payroll.compute()
        db.add(payroll)
        db.flush()

        elapsed = round((time.time() - start) * 1000, 2)
        db.add(QualityLog(
            module="PAYROLL",
            action="PAYROLL_GENERATED",
            status="SUCCESS",
            execution_time_ms=elapsed,
            details=f"Payroll for '{user.full_name}' ({target_month}/{target_year}): Gross Rs. {payroll.gross_salary}, Net Rs. {payroll.net_salary}",
        ))

        logger.info(f"Payroll generated for {user.full_name}: Net Rs. {payroll.net_salary}")
        return {
            "success": True,
            "message": f"Payroll generated for {user.full_name}.",
            "payroll_id": payroll.id,
            "gross_salary": payroll.gross_salary,
            "deductions": payroll.deductions,
            "net_salary": payroll.net_salary,
        }


def get_payroll_summary() -> list:
    """Returns all payroll records with staff names for display."""
    with get_db() as db:
        payrolls = db.scalars(select(StaffPayroll)).all()
        results = []
        for p in payrolls:
            results.append({
                "id": p.id,
                "staff_name": p.user.full_name,
                "period": f"{p.period_month}/{p.period_year}",
                "regular_hours": p.total_regular_hours,
                "overtime_hours": p.total_overtime_hours,
                "gross": p.gross_salary,
                "deductions": p.deductions,
                "net": p.net_salary,
                "status": p.status,
            })
        return results


def get_staff_shifts(user_id: int) -> list:
    """Returns all shifts for a given staff member."""
    with get_db() as db:
        shifts = db.scalars(
            select(StaffShift).where(StaffShift.user_id == user_id).order_by(StaffShift.shift_date.desc())
        ).all()
        return [{
            "id": s.id,
            "date": str(s.shift_date),
            "type": s.shift_type,
            "regular": s.regular_hours,
            "overtime": s.overtime_hours,
            "total": s.total_hours(),
            "tasks": s.tasks_completed,
            "verified": s.is_verified,
        } for s in shifts]
