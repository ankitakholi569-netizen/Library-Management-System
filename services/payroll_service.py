"""
Automated Payroll Processing & Shift Management Service.
Course: BBAT104 - Total Quality Management.
Core TQM Objective: Eliminate manual payroll errors through automated shift aggregation,
overtime factor calculation, and tax withholding compliance.
"""

from datetime import date, datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import select, func, and_
from database.db import get_db
from database.models import User, StaffShift, StaffPayroll
from config.settings import TQM_CONFIG
from services.logger_service import get_logger, log_quality_event, timed_operation

logger = get_logger("payroll_service")


# ==============================================================================
# 1. SHIFT LOGGING & ATTENDANCE
# ==============================================================================
def log_shift(
    user_id: int,
    shift_date: Optional[date] = None,
    regular_hours: float = 8.0,
    overtime_hours: float = 0.0,
    shift_type: str = "Regular Day Shift",
    tasks_completed: str = "General library circulation and catalog maintenance",
    is_verified: bool = True,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Records a completed staff shift for payroll calculation with full field validation.
    """
    if not user_id:
        return False, None, "Staff user ID is required."
    try:
        user_id = int(user_id)
        if user_id <= 0:
            return False, None, "Staff user ID must be a positive integer."
    except (ValueError, TypeError):
        return False, None, "Invalid staff user ID format."

    try:
        regular_hours = float(regular_hours)
        overtime_hours = float(overtime_hours)
    except (ValueError, TypeError):
        return False, None, "Working hours must be valid numbers."

    if regular_hours < 0 or overtime_hours < 0:
        return False, None, "Working hours cannot be negative."

    if regular_hours + overtime_hours <= 0:
        return False, None, "Total shift hours (regular + overtime) must be greater than zero."

    if regular_hours + overtime_hours > 24.0:
        return False, None, "Total shift hours cannot exceed 24 hours in a single day."

    tasks_completed = (tasks_completed or "").strip()
    if not tasks_completed:
        return False, None, "Task summary description is required."
    if len(tasks_completed) < 3:
        return False, None, "Task summary must be at least 3 characters long."

    shift_type = (shift_type or "").strip() or "Regular Day Shift"
    target_date = shift_date or date.today()

    with timed_operation("PAYROLL", "LOG_SHIFT", details=f"User ID: {user_id}, Date: {target_date}"):
        with get_db() as db:
            user = db.get(User, user_id)
            if not user:
                return False, None, f"Staff user with ID {user_id} not found."

            shift = StaffShift(
                user_id=user_id,
                shift_date=target_date,
                shift_type=shift_type,
                regular_hours=float(regular_hours),
                overtime_hours=float(overtime_hours),
                tasks_completed=tasks_completed,
                is_verified=bool(is_verified),
            )
            db.add(shift)
            db.flush()
            shift_dict = shift.to_dict()

        logger.info(f"Shift logged for {user.full_name}: {regular_hours}h regular + {overtime_hours}h OT.")
        return True, shift_dict, "Shift logged successfully."


def get_staff_shifts(
    user_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves logged shifts filtered by user and/or month/year.
    """
    with get_db() as db:
        query = select(StaffShift).order_by(StaffShift.shift_date.desc())
        conditions = []

        if user_id is not None:
            conditions.append(StaffShift.user_id == user_id)

        if conditions:
            query = query.where(and_(*conditions))

        shifts = db.scalars(query).all()
        results = []
        for s in shifts:
            if month and s.shift_date.month != month:
                continue
            if year and s.shift_date.year != year:
                continue
            results.append(s.to_dict())

        return results


# ==============================================================================
# 2. AUTOMATED PAYROLL COMPUTATION ENGINE
# ==============================================================================
def generate_monthly_payroll(
    user_id: int,
    period_month: int,
    period_year: int,
    custom_rate: Optional[float] = None,
    custom_deduction_rate: Optional[float] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    TQM Core Automation:
    Aggregates verified shifts for the period, computes regular & overtime earnings,
    calculates deductions, and records a standardized StaffPayroll entry.
    """
    try:
        user_id = int(user_id)
        if user_id <= 0:
            return False, None, "Valid staff user ID is required."
        period_month = int(period_month)
        period_year = int(period_year)
    except (ValueError, TypeError):
        return False, None, "Invalid parameters for payroll calculation."

    if not (1 <= period_month <= 12):
        return False, None, "Invalid month. Must be between 1 and 12."
    if period_year < 2000 or period_year > 2099:
        return False, None, "Invalid year. Must be between 2000 and 2099."

    with timed_operation("PAYROLL", "GENERATE_PAYROLL", details=f"User: {user_id}, Period: {period_month}/{period_year}"):
        with get_db() as db:
            user = db.get(User, user_id)
            if not user:
                return False, None, f"Staff user ID {user_id} not found."

            # Fetch all shifts for user in target period
            all_shifts = db.scalars(
                select(StaffShift).where(
                    and_(
                        StaffShift.user_id == user_id,
                        StaffShift.is_verified == True,
                    )
                )
            ).all()

            period_shifts = [
                s for s in all_shifts
                if s.shift_date.month == period_month and s.shift_date.year == period_year
            ]

            total_reg = sum(s.regular_hours for s in period_shifts)
            total_ot = sum(s.overtime_hours for s in period_shifts)

            # If no logged shifts, provide standard base hours for salaried staff (160h)
            if total_reg == 0 and total_ot == 0:
                total_reg = 160.0
                total_ot = 0.0

            rate = custom_rate if custom_rate is not None else user.hourly_rate
            deduction_rate = custom_deduction_rate if custom_deduction_rate is not None else TQM_CONFIG["TAX_DEDUCTION_RATE"]
            ot_multiplier = TQM_CONFIG["OVERTIME_MULTIPLIER"]

            reg_amount = round(total_reg * rate, 2)
            ot_amount = round(total_ot * rate * ot_multiplier, 2)
            gross = round(reg_amount + ot_amount, 2)
            deductions = round(gross * deduction_rate, 2)
            net = round(gross - deductions, 2)

            # Check if payroll already exists for this period
            existing_payroll = db.scalar(
                select(StaffPayroll).where(
                    and_(
                        StaffPayroll.user_id == user_id,
                        StaffPayroll.period_month == period_month,
                        StaffPayroll.period_year == period_year,
                    )
                )
            )

            if existing_payroll:
                payroll = existing_payroll
                payroll.total_regular_hours = total_reg
                payroll.total_overtime_hours = total_ot
                payroll.hourly_rate = rate
                payroll.regular_amount = reg_amount
                payroll.overtime_amount = ot_amount
                payroll.gross_salary = gross
                payroll.deductions = deductions
                payroll.net_salary = net
                payroll.processed_at = datetime.utcnow()
            else:
                payroll = StaffPayroll(
                    user_id=user_id,
                    period_month=period_month,
                    period_year=period_year,
                    total_regular_hours=total_reg,
                    total_overtime_hours=total_ot,
                    hourly_rate=rate,
                    regular_amount=reg_amount,
                    overtime_amount=ot_amount,
                    gross_salary=gross,
                    deductions=deductions,
                    net_salary=net,
                    performance_rating=4.8,
                    status="Processed",
                )
                db.add(payroll)

            db.flush()
            result_dict = payroll.to_dict()

        logger.info(
            f"Payroll computed for {user.full_name} ({period_month}/{period_year}): "
            f"Gross: Rs.{gross:.2f}, Deductions: Rs.{deductions:.2f}, Net: Rs.{net:.2f}"
        )
        return True, result_dict, "Payroll successfully calculated."


def generate_all_staff_payrolls(
    period_month: int,
    period_year: int,
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Automates bulk payroll calculation for all staff members with period validation.
    """
    try:
        period_month = int(period_month)
        period_year = int(period_year)
    except (ValueError, TypeError):
        return 0, []

    if not (1 <= period_month <= 12) or period_year < 2000 or period_year > 2099:
        return 0, []

    generated = []
    with get_db() as db:
        users = db.scalars(
            select(User).where(User.role.in_(["Chief Librarian", "Assistant Librarian", "Library Assistant"]))
        ).all()
        user_ids = [u.id for u in users]

    for uid in user_ids:
        ok, data, _ = generate_monthly_payroll(uid, period_month, period_year)
        if ok and data:
            generated.append(data)

    log_quality_event(
        "PAYROLL",
        "BULK_PAYROLL_RUN",
        "SUCCESS",
        details=f"Generated {len(generated)} payroll records for period {period_month}/{period_year}",
    )
    return len(generated), generated


def get_all_payrolls(
    period_month: Optional[int] = None,
    period_year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves all computed payroll records.
    """
    with get_db() as db:
        query = select(StaffPayroll).order_by(StaffPayroll.period_year.desc(), StaffPayroll.period_month.desc())
        conditions = []
        if period_month:
            conditions.append(StaffPayroll.period_month == period_month)
        if period_year:
            conditions.append(StaffPayroll.period_year == period_year)
        if conditions:
            query = query.where(and_(*conditions))

        payrolls = db.scalars(query).all()
        return [p.to_dict() for p in payrolls]


def get_payroll_by_id(payroll_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single payroll record by ID."""
    if not payroll_id or int(payroll_id) <= 0:
        return None
    with get_db() as db:
        payroll = db.get(StaffPayroll, int(payroll_id))
        return payroll.to_dict() if payroll else None


def update_payroll_status(payroll_id: int, status: str) -> bool:
    """Updates the status of a payroll (Processed, Approved, Disbursed)."""
    status = (status or "").strip()
    valid_statuses = ["Processed", "Approved", "Paid", "Disbursed", "Pending"]
    if status not in valid_statuses:
        return False

    with get_db() as db:
        payroll = db.get(StaffPayroll, int(payroll_id))
        if not payroll:
            return False
        payroll.status = status
        db.flush()
    log_quality_event("PAYROLL", "STATUS_UPDATE", "SUCCESS", details=f"Payroll {payroll_id} status -> {status}")
    return True
