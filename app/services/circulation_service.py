"""
Circulation Service — Book Issue, Return & Fine Settlement Logic.
Demonstrates TQM Principle: Process Automation & Accuracy.
"""

from datetime import date, timedelta
from sqlalchemy import select, func
from app.models.base import get_db
from app.models.book import Book
from app.models.member import Member
from app.models.loan import Loan
from app.models.quality_log import QualityLog
from app.config import TQM_CONFIG
from app.core.logger import get_logger
import time

logger = get_logger("circulation")


def issue_book(book_id: int, member_id: int, processed_by: str = "Librarian") -> dict:
    """
    Issues a book to a member after validating eligibility and availability.
    Demonstrates TQM Error Prevention & Process Standardization.
    """
    start = time.time()
    with get_db() as db:
        book = db.get(Book, book_id)
        member = db.get(Member, member_id)

        if not book:
            return {"success": False, "message": f"Book ID {book_id} not found in catalog."}
        if not member:
            return {"success": False, "message": f"Member ID {member_id} not found in directory."}

        # TQM Eligibility Check
        can_borrow, reason = member.can_borrow()
        if not can_borrow:
            return {"success": False, "message": reason}

        # Availability Check
        if not book.borrow_copy():
            return {"success": False, "message": f"'{book.title}' is currently out of stock (0/{book.total_copies} available)."}

        # Create Loan Record
        today = date.today()
        loan = Loan(
            book_id=book.id,
            member_id=member.id,
            issue_date=today,
            due_date=today + timedelta(days=TQM_CONFIG["LOAN_PERIOD_DAYS"]),
            status="Borrowed",
            fine_amount=0.0,
            processed_by=processed_by,
        )
        db.add(loan)
        db.flush()

        elapsed = round((time.time() - start) * 1000, 2)
        # TQM Quality Log
        db.add(QualityLog(
            module="CIRCULATION",
            action="BOOK_ISSUED",
            status="SUCCESS",
            execution_time_ms=elapsed,
            details=f"Book '{book.title}' issued to '{member.name}' (USN: {member.usn}). Due: {loan.due_date}",
        ))

        logger.info(f"Book issued: '{book.title}' -> {member.name} (Due: {loan.due_date})")
        return {
            "success": True,
            "message": f"'{book.title}' issued to {member.name}. Due date: {loan.due_date}",
            "loan_id": loan.id,
            "due_date": str(loan.due_date),
        }


def return_book(loan_id: int) -> dict:
    """
    Processes a book return, calculates fines if overdue, and updates inventory.
    Demonstrates TQM Process Automation & SLA Compliance.
    """
    start = time.time()
    with get_db() as db:
        loan = db.get(Loan, loan_id)
        if not loan:
            return {"success": False, "message": f"Loan ID {loan_id} not found."}
        if loan.status == "Returned":
            return {"success": False, "message": f"Loan #{loan_id} has already been returned."}

        today = date.today()
        loan.return_date = today
        loan.status = "Returned"

        # Calculate fine if overdue
        fine = 0.0
        overdue_days = loan.days_overdue(as_of=today)
        if overdue_days > 0:
            fine = round(overdue_days * TQM_CONFIG["FINE_PER_DAY"], 2)
            loan.fine_amount = fine

        # Return copy to inventory
        book = db.get(Book, loan.book_id)
        if book:
            book.return_copy()

        elapsed = round((time.time() - start) * 1000, 2)
        status_tag = "SLA_BREACH" if overdue_days > 0 else "SUCCESS"
        db.add(QualityLog(
            module="CIRCULATION",
            action="BOOK_RETURNED",
            status=status_tag,
            execution_time_ms=elapsed,
            details=f"Loan #{loan_id} returned. Overdue: {overdue_days} days. Fine: Rs. {fine}",
        ))

        logger.info(f"Book returned: Loan #{loan_id}, Overdue: {overdue_days} days, Fine: Rs. {fine}")
        return {
            "success": True,
            "message": f"Book returned successfully. {'Fine: Rs. ' + str(fine) if fine > 0 else 'No fine — returned on time.'}",
            "overdue_days": overdue_days,
            "fine": fine,
        }


def settle_fine(loan_id: int) -> dict:
    """Marks a fine as paid for the given loan."""
    with get_db() as db:
        loan = db.get(Loan, loan_id)
        if not loan:
            return {"success": False, "message": f"Loan ID {loan_id} not found."}
        if loan.fine_amount <= 0:
            return {"success": False, "message": "No fine to settle on this loan."}
        if loan.fine_paid:
            return {"success": False, "message": "Fine has already been paid."}

        loan.fine_paid = True
        logger.info(f"Fine settled for Loan #{loan_id}: Rs. {loan.fine_amount}")
        return {
            "success": True,
            "message": f"Fine of Rs. {loan.fine_amount} settled for Loan #{loan_id}.",
        }


def refresh_overdue_status() -> int:
    """
    Scans all active loans and updates overdue status & fines.
    Returns count of overdue loans found.
    """
    overdue_count = 0
    with get_db() as db:
        active_loans = db.scalars(
            select(Loan).where(Loan.status.in_(["Borrowed", "Overdue"]))
        ).all()
        for loan in active_loans:
            loan.check_and_update_overdue()
            if loan.status == "Overdue":
                overdue_count += 1
    logger.info(f"Overdue refresh complete: {overdue_count} overdue loans detected.")
    return overdue_count


def get_circulation_summary() -> dict:
    """Returns a summary of circulation statistics for dashboard display."""
    with get_db() as db:
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
        total_fines = db.scalar(
            select(func.sum(Loan.fine_amount)).where(Loan.fine_amount > 0)
        ) or 0.0

        return {
            "total_loans": total_loans,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "returned_loans": returned_loans,
            "total_fines_collected": round(total_fines, 2),
        }
