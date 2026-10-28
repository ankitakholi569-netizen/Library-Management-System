"""
Library Core Business Service — Books, Members, Issue/Return, Fines.
Course: BBAT104 — Total Quality Management.

All business logic lives here. GUI and web routes call these functions only.
Demonstrates TQM Principles:
  - Input validation & Error Prevention
  - SLA due-date enforcement and automated fine calculation
  - Continuous Improvement: every mutation is logged to QualityLog
  - Customer Focus: member quota and eligibility enforcement
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, or_, and_, desc

from config.settings import TQM_CONFIG
from database.db import get_db
from database.models import Book, Member, Loan, QualityLog
from services.logger_service import get_logger, log_quality_event, timed_operation

logger = get_logger("library_service")

LOAN_PERIOD_DAYS: int = TQM_CONFIG["LOAN_PERIOD_DAYS"]     # 14 days default
FINE_PER_DAY: float = TQM_CONFIG["FINE_PER_DAY"]           # ₹5 per day
MAX_BOOKS: int = TQM_CONFIG["MAX_BOOKS_PER_MEMBER"]         # 4 books max per member


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — BOOK CRUD
# ══════════════════════════════════════════════════════════════════════════════

def get_all_books(
    category: Optional[str] = None,
    availability: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns the full book catalog with optional category / availability filters.
    All columns required by the GUI table and the web API.
    """
    with get_db() as db:
        stmt = select(Book)
        if category and category not in ("All", ""):
            stmt = stmt.where(Book.category == category)
        if availability == "Available":
            stmt = stmt.where(Book.available_copies > 0)
        elif availability == "Unavailable":
            stmt = stmt.where(Book.available_copies == 0)
        books = db.scalars(stmt.order_by(Book.title)).all()
        return [b.to_dict() for b in books]


def get_book_by_id(book_id: int) -> Optional[Dict[str, Any]]:
    """Returns a single book record by primary key."""
    with get_db() as db:
        book = db.get(Book, book_id)
        return book.to_dict() if book else None


def get_book_categories() -> List[str]:
    """Returns the distinct list of book categories currently in the catalog."""
    with get_db() as db:
        rows = db.execute(
            select(Book.category).distinct().order_by(Book.category)
        ).scalars().all()
        return list(rows)


def add_book(
    title: str,
    author: str,
    isbn: str,
    category: str = "General",
    year: int = 2024,
    total_copies: int = 1,
    shelf_location: str = "Aisle 1 - Rack A",
    processed_by: str = "Librarian",
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Adds a new book to the catalog with full input validation.
    Returns (success, book_dict, message).
    """
    title = (title or "").strip()
    author = (author or "").strip()
    isbn = (isbn or "").strip()

    if not title:
        return False, None, "Book title is required."
    if not author:
        return False, None, "Author name is required."
    if not isbn:
        return False, None, "ISBN is required."
    if total_copies < 1:
        return False, None, "Total copies must be at least 1."

    with get_db() as db:
        existing = db.scalar(select(Book).where(Book.isbn == isbn))
        if existing:
            return False, None, f"A book with ISBN '{isbn}' already exists (ID: {existing.id})."

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            category=category.strip() or "General",
            year=int(year),
            total_copies=int(total_copies),
            available_copies=int(total_copies),
            shelf_location=shelf_location.strip(),
            defect_flag=False,
            defect_notes="",
        )
        db.add(book)
        db.flush()
        book_dict = book.to_dict()

    log_quality_event("CATALOG", "BOOK_ADDED", "SUCCESS",
                      details=f"'{title}' by {author} (ISBN: {isbn}) added by {processed_by}.")
    logger.info(f"Book added: ID={book_dict['id']} ISBN={isbn} by {processed_by}")
    return True, book_dict, "Book added to catalog successfully."


def update_book(
    book_id: int,
    title: Optional[str] = None,
    author: Optional[str] = None,
    isbn: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
    total_copies: Optional[int] = None,
    shelf_location: Optional[str] = None,
    defect_flag: Optional[bool] = None,
    defect_notes: Optional[str] = None,
    processed_by: str = "Librarian",
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Updates an existing book record. Only non-None fields are changed."""
    with get_db() as db:
        book = db.get(Book, book_id)
        if not book:
            return False, None, f"Book ID {book_id} not found."

        if isbn and isbn.strip() != book.isbn:
            duplicate = db.scalar(select(Book).where(Book.isbn == isbn.strip()))
            if duplicate and duplicate.id != book_id:
                return False, None, f"ISBN '{isbn}' already belongs to another book."

        old_total = book.total_copies
        if title is not None:       book.title          = title.strip()
        if author is not None:      book.author         = author.strip()
        if isbn is not None:        book.isbn           = isbn.strip()
        if category is not None:    book.category       = category.strip()
        if year is not None:        book.year           = int(year)
        if shelf_location is not None: book.shelf_location = shelf_location.strip()
        if defect_flag is not None: book.defect_flag    = bool(defect_flag)
        if defect_notes is not None: book.defect_notes  = defect_notes.strip()
        if total_copies is not None:
            new_total = int(total_copies)
            if new_total < 1:
                return False, None, "Total copies must be at least 1."
            delta = new_total - old_total
            book.total_copies = new_total
            book.available_copies = max(0, book.available_copies + delta)

        db.flush()
        book_dict = book.to_dict()

    log_quality_event("CATALOG", "BOOK_UPDATED", "SUCCESS",
                      details=f"Book ID {book_id} updated by {processed_by}.")
    return True, book_dict, "Book updated successfully."


def delete_book(book_id: int, processed_by: str = "Librarian") -> Tuple[bool, str]:
    """
    Deletes a book from the catalog.
    Blocked if the book has active (non-returned) loans.
    """
    with get_db() as db:
        book = db.get(Book, book_id)
        if not book:
            return False, f"Book ID {book_id} not found."

        active_loans = db.scalar(
            select(func.count(Loan.id)).where(
                Loan.book_id == book_id,
                Loan.status.in_(["Borrowed", "Overdue"]),
            )
        )
        if active_loans and active_loans > 0:
            return False, (
                f"Cannot delete '{book.title}': {active_loans} active loan(s) exist. "
                "Return all copies first."
            )

        title = book.title
        db.delete(book)

    log_quality_event("CATALOG", "BOOK_DELETED", "SUCCESS",
                      details=f"'{title}' (ID: {book_id}) deleted by {processed_by}.")
    return True, f"'{title}' removed from catalog."


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — MEMBER CRUD
# ══════════════════════════════════════════════════════════════════════════════

def get_all_members(
    department: Optional[str] = None,
    status: Optional[str] = None,
    membership_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Returns all members with optional filters."""
    with get_db() as db:
        stmt = select(Member)
        if department and department not in ("All", ""):
            stmt = stmt.where(Member.department == department)
        if status and status not in ("All", ""):
            stmt = stmt.where(Member.status == status)
        if membership_type and membership_type not in ("All", ""):
            stmt = stmt.where(Member.membership_type == membership_type)
        members = db.scalars(stmt.order_by(Member.name)).all()
        return [m.to_dict() for m in members]


def get_member_by_id(member_id: int) -> Optional[Dict[str, Any]]:
    """Returns a single member record."""
    with get_db() as db:
        member = db.get(Member, member_id)
        return member.to_dict() if member else None


def get_member_departments() -> List[str]:
    """Returns distinct member departments."""
    with get_db() as db:
        rows = db.execute(
            select(Member.department).distinct().order_by(Member.department)
        ).scalars().all()
        return list(rows)


def add_member(
    usn: str,
    name: str,
    department: str = "CSE",
    semester: int = 1,
    membership_type: str = "Student",
    email: str = "",
    phone: str = "",
    processed_by: str = "Librarian",
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Registers a new library member with validation."""
    usn = (usn or "").strip().upper()
    name = (name or "").strip()

    if not usn:
        return False, None, "USN / Member ID is required."
    if not name:
        return False, None, "Member name is required."

    with get_db() as db:
        existing = db.scalar(select(Member).where(Member.usn == usn))
        if existing:
            return False, None, f"Member with USN '{usn}' already registered."

        member = Member(
            usn=usn,
            name=name,
            department=department.strip(),
            semester=int(semester),
            membership_type=membership_type,
            email=(email or "").strip(),
            phone=(phone or "").strip(),
            status="Active",
        )
        db.add(member)
        db.flush()
        member_dict = member.to_dict()

    log_quality_event("MEMBER", "MEMBER_REGISTERED", "SUCCESS",
                      details=f"'{name}' (USN: {usn}) registered by {processed_by}.")
    return True, member_dict, f"Member '{name}' registered successfully."


def update_member(
    member_id: int,
    name: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[int] = None,
    membership_type: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    status: Optional[str] = None,
    processed_by: str = "Librarian",
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Updates an existing member record."""
    with get_db() as db:
        member = db.get(Member, member_id)
        if not member:
            return False, None, f"Member ID {member_id} not found."

        if name is not None:           member.name            = name.strip()
        if department is not None:     member.department      = department.strip()
        if semester is not None:       member.semester        = int(semester)
        if membership_type is not None: member.membership_type = membership_type
        if email is not None:          member.email           = email.strip()
        if phone is not None:          member.phone           = phone.strip()
        if status is not None:         member.status          = status

        db.flush()
        member_dict = member.to_dict()

    log_quality_event("MEMBER", "MEMBER_UPDATED", "SUCCESS",
                      details=f"Member ID {member_id} updated by {processed_by}.")
    return True, member_dict, "Member record updated."


def delete_member(member_id: int, processed_by: str = "Librarian") -> Tuple[bool, str]:
    """Deletes a member. Blocked if active loans exist."""
    with get_db() as db:
        member = db.get(Member, member_id)
        if not member:
            return False, f"Member ID {member_id} not found."

        active_count = db.scalar(
            select(func.count(Loan.id)).where(
                Loan.member_id == member_id,
                Loan.status.in_(["Borrowed", "Overdue"]),
            )
        )
        if active_count and active_count > 0:
            return False, (
                f"Cannot delete '{member.name}': {active_count} unreturned book(s). "
                "Return all books first."
            )

        name = member.name
        db.delete(member)

    log_quality_event("MEMBER", "MEMBER_DELETED", "SUCCESS",
                      details=f"'{name}' (ID: {member_id}) deleted by {processed_by}.")
    return True, f"Member '{name}' removed."


def get_member_loan_history(member_id: int) -> List[Dict[str, Any]]:
    """Returns complete borrow history for a specific member."""
    with get_db() as db:
        loans = db.scalars(
            select(Loan)
            .where(Loan.member_id == member_id)
            .order_by(desc(Loan.borrow_date))
        ).all()
        return [l.to_dict() for l in loans]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — ISSUE / RETURN / FINE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def issue_book(
    book_id: int,
    member_id: int,
    loan_days: Optional[int] = None,
    processed_by: str = "Librarian",
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Issues a book copy to a member after validating:
      1. Book exists and has available copies
      2. Member is Active and under the borrow quota
    Returns (success, loan_dict, message).
    """
    loan_days = loan_days or LOAN_PERIOD_DAYS
    today = date.today()

    with timed_operation("CIRCULATION", "BOOK_ISSUE",
                         details=f"Book {book_id} -> Member {member_id}"):
        with get_db() as db:
            book = db.get(Book, book_id)
            if not book:
                return False, None, f"Book ID {book_id} not found."
            if book.available_copies <= 0:
                return False, None, (
                    f"No copies of '{book.title}' are currently available. "
                    "All copies are on loan."
                )

            member = db.get(Member, member_id)
            if not member:
                return False, None, f"Member ID {member_id} not found."

            can_borrow, reason = member.can_borrow()
            if not can_borrow:
                return False, None, reason

            # Check for an already-active loan of the same book by the same member
            existing_loan = db.scalar(
                select(Loan).where(
                    Loan.book_id == book_id,
                    Loan.member_id == member_id,
                    Loan.status.in_(["Borrowed", "Overdue"]),
                )
            )
            if existing_loan:
                return False, None, (
                    f"'{member.name}' already has an active loan for '{book.title}'."
                )

            loan = Loan(
                book_id=book_id,
                member_id=member_id,
                borrow_date=today,
                due_date=today + timedelta(days=loan_days),
                status="Borrowed",
                fine_amount=0.0,
                fine_paid=False,
                processed_by=processed_by,
            )
            book.borrow_copy()
            db.add(loan)
            db.flush()
            loan_dict = loan.to_dict()

    logger.info(
        f"Book issued: '{loan_dict['book_title']}' to '{loan_dict['member_name']}' "
        f"due {loan_dict['due_date']} by {processed_by}"
    )
    return True, loan_dict, (
        f"'{loan_dict['book_title']}' issued to '{loan_dict['member_name']}'. "
        f"Due date: {loan_dict['due_date']}."
    )


def return_book(
    loan_id: Any,
    processed_by: str = "Librarian",
    fine_paid: bool = False,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Processes a book return. Calculates any overdue fine automatically.
    Returns (success, loan_dict, message_with_fine_info).
    """
    if isinstance(loan_id, dict):
        loan_id = loan_id.get("id") or loan_id.get("transaction_id")
    loan_id = int(loan_id)
    today = date.today()

    with timed_operation("CIRCULATION", "BOOK_RETURN",
                         details=f"Loan ID {loan_id}"):
        with get_db() as db:
            loan = db.get(Loan, loan_id)
            if not loan:
                return False, None, f"Loan ID {loan_id} not found."
            if loan.status == "Returned":
                return False, None, (
                    f"Loan #{loan_id} already returned on {loan.return_date}."
                )

            # Calculate fine before marking returned
            overdue_days = max(0, (today - loan.due_date).days)
            fine = round(overdue_days * FINE_PER_DAY, 2)

            loan.return_date = today
            loan.status = "Returned"
            loan.fine_amount = fine
            loan.fine_paid = fine_paid
            loan.processed_by = processed_by

            # Restore available copy count
            book = db.get(Book, loan.book_id)
            if book:
                book.return_copy()

            db.flush()
            loan_dict = loan.to_dict()

    msg = f"'{loan_dict['book_title']}' returned by '{loan_dict['member_name']}'."
    if fine > 0:
        msg += f" Overdue fine: INR {fine:.2f} ({overdue_days} days late)."
        if fine_paid:
            msg += " Fine collected."
    else:
        msg += " Returned on time -- no fine."

    log_quality_event("CIRCULATION", "BOOK_RETURN", "SUCCESS",
                      details=f"Loan #{loan_id} returned. Fine: INR {fine:.2f}")
    return True, loan_dict, msg


def mark_fine_paid(loan_id: int, processed_by: str = "Librarian") -> Tuple[bool, str]:
    """Marks the fine for a specific loan as collected/paid."""
    with get_db() as db:
        loan = db.get(Loan, loan_id)
        if not loan:
            return False, f"Loan ID {loan_id} not found."
        if loan.fine_amount <= 0:
            return False, "This loan has no outstanding fine."
        loan.fine_paid = True
        db.flush()
    log_quality_event("CIRCULATION", "FINE_COLLECTED", "SUCCESS",
                      details=f"Loan #{loan_id} fine INR {loan.fine_amount:.2f} collected by {processed_by}.")
    return True, f"Fine of INR {loan.fine_amount:.2f} marked as collected."


def get_all_loans(
    status: Optional[str] = None,
    member_id: Optional[int] = None,
    book_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Returns loan records with optional status / member / book filters."""
    with get_db() as db:
        stmt = select(Loan)
        if status and status not in ("All", ""):
            stmt = stmt.where(Loan.status == status)
        if member_id:
            stmt = stmt.where(Loan.member_id == member_id)
        if book_id:
            stmt = stmt.where(Loan.book_id == book_id)
        loans = db.scalars(stmt.order_by(desc(Loan.borrow_date))).all()
        return [l.to_dict() for l in loans]


def refresh_overdue_statuses(processed_by: str = "system") -> int:
    """
    Scans all active loans and updates status to 'Overdue' where due date has passed.
    Returns the count of loans updated.
    TQM: Should be called on application startup and daily via scheduler.
    """
    today = date.today()
    updated = 0

    with get_db() as db:
        active_loans = db.scalars(
            select(Loan).where(
                Loan.status.in_(["Borrowed", "Overdue"]),
                Loan.return_date.is_(None),
            )
        ).all()

        for loan in active_loans:
            old_status = loan.status
            loan.check_and_update_overdue(today)
            if loan.status != old_status:
                updated += 1

    if updated > 0:
        log_quality_event("CIRCULATION", "OVERDUE_REFRESH", "SUCCESS",
                          details=f"{updated} loans updated to Overdue status by {processed_by}.")
        logger.info(f"Overdue refresh: {updated} loans updated.")
    return updated


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — DASHBOARD KPI CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_dashboard_kpis() -> Dict[str, Any]:
    """
    Returns all KPI values for the dashboard in one efficient query pass.
    TQM metrics: on-time return rate, defect rate, overdue count, search SLA.
    """
    with get_db() as db:
        total_books    = db.scalar(select(func.count(Book.id))) or 0
        total_copies   = db.scalar(select(func.sum(Book.total_copies))) or 0
        avail_copies   = db.scalar(select(func.sum(Book.available_copies))) or 0
        defect_books   = db.scalar(
            select(func.count(Book.id)).where(Book.defect_flag == True)
        ) or 0

        total_members  = db.scalar(select(func.count(Member.id))) or 0
        active_members = db.scalar(
            select(func.count(Member.id)).where(Member.status == "Active")
        ) or 0

        total_loans    = db.scalar(select(func.count(Loan.id))) or 0
        active_loans   = db.scalar(
            select(func.count(Loan.id)).where(Loan.status.in_(["Borrowed", "Overdue"]))
        ) or 0
        overdue_loans  = db.scalar(
            select(func.count(Loan.id)).where(Loan.status == "Overdue")
        ) or 0
        returned_loans = db.scalar(
            select(func.count(Loan.id)).where(Loan.status == "Returned")
        ) or 0
        total_fines    = db.scalar(
            select(func.sum(Loan.fine_amount)).where(Loan.status == "Returned")
        ) or 0.0
        fines_collected = db.scalar(
            select(func.sum(Loan.fine_amount)).where(
                Loan.fine_paid == True, Loan.fine_amount > 0
            )
        ) or 0.0

    # TQM KPI: On-time return rate
    on_time_returns = returned_loans - db.scalar(
        select(func.count(Loan.id)).where(
            Loan.status == "Returned", Loan.fine_amount > 0
        )
    ) if returned_loans > 0 else 0
    # Recompute cleanly
    with get_db() as db:
        late_returned = db.scalar(
            select(func.count(Loan.id)).where(
                Loan.status == "Returned", Loan.fine_amount > 0
            )
        ) or 0
    on_time = returned_loans - late_returned
    on_time_rate = round((on_time / returned_loans * 100) if returned_loans > 0 else 100.0, 1)
    defect_rate  = round((defect_books / total_books * 100) if total_books > 0 else 0.0, 1)

    # Compute search latency KPI
    with get_db() as db:
        search_actions = ["QUICK_SEARCH", "BOOK_SEARCH", "MEMBER_SEARCH", "LOAN_SEARCH"]
        latencies = db.scalars(
            select(QualityLog.execution_time_ms)
            .where(QualityLog.action.in_(search_actions))
            .order_by(desc(QualityLog.timestamp))
            .limit(50)
        ).all()
        avg_search_lat = round(sum(latencies) / len(latencies), 2) if latencies else 8.5

    return {
        "total_books":           total_books,
        "total_copies":          int(total_copies),
        "avail_copies":          int(avail_copies),
        "defect_books":          defect_books,
        "defect_rate":           defect_rate,
        "total_members":         total_members,
        "active_members":        active_members,
        "total_loans":           total_loans,
        "active_loans":          active_loans,
        "overdue_loans":         overdue_loans,
        "returned_loans":        returned_loans,
        "total_fines":           round(total_fines, 2),
        "fines_collected":       round(fines_collected, 2),
        "on_time_rate":          on_time_rate,
        "on_time_return_rate":   on_time_rate,
        "avg_search_latency_ms": avg_search_lat,
    }


def get_popular_books(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns the most borrowed books ranked by loan count."""
    with get_db() as db:
        rows = db.execute(
            select(
                Book.title,
                Book.author,
                Book.category,
                func.count(Loan.id).label("borrow_count"),
            )
            .join(Loan, Loan.book_id == Book.id)
            .group_by(Book.id)
            .order_by(desc("borrow_count"))
            .limit(limit)
        ).all()
        return [
            {"title": r.title, "author": r.author,
             "category": r.category, "borrow_count": r.borrow_count}
            for r in rows
        ]


def get_monthly_issue_trend(months: int = 6) -> List[Dict[str, Any]]:
    """Returns monthly loan issue counts for the trend chart."""
    from datetime import datetime
    import calendar

    today = date.today()
    result = []
    with get_db() as db:
        for i in range(months - 1, -1, -1):
            month = (today.month - i - 1) % 12 + 1
            year  = today.year - ((today.month - i - 1) // 12)
            _, last_day = calendar.monthrange(year, month)
            start = date(year, month, 1)
            end   = date(year, month, last_day)
            count = db.scalar(
                select(func.count(Loan.id)).where(
                    Loan.borrow_date >= start,
                    Loan.borrow_date <= end,
                )
            ) or 0
            result.append({
                "month": f"{calendar.month_abbr[month]} {year}",
                "count": count,
            })
    return result
