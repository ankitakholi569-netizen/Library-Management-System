"""
Search & Retrieval Service — Quality Goal 1 Implementation.
Course: BBAT104 — Total Quality Management.

Provides instant search across all entities with:
  - Multi-column full-text matching (title, author, ISBN, name, USN)
  - Advanced filter composition (category, dept, availability, status, date range)
  - Multi-column sorting and cursor-based pagination
  - Millisecond response timing recorded as a quality KPI in QualityLog
  - SLA breach detection when query exceeds 100ms threshold

All queries use the B-Tree indexes defined in database/models.py.
"""

from __future__ import annotations

import time
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, or_, and_, desc, asc, text

from config.settings import TQM_CONFIG
from database.db import get_db
from database.models import Book, Member, Loan, QualityLog
from services.logger_service import get_logger, log_quality_event

logger = get_logger("search_service")

SLA_MS: float = TQM_CONFIG["MAX_QUERY_LATENCY_MS"]   # 100 ms


# ── Helpers ──────────────────────────────────────────────────────────────────

def _record_search_kpi(module: str, action: str, latency_ms: float,
                       result_count: int, query_text: str = ""):
    """Records search response time in QualityLog for the KPI dashboard."""
    status = "SLA_BREACH" if latency_ms > SLA_MS else "SUCCESS"
    remedial = (
        "Investigate DB index and optimize search query"
        if status == "SLA_BREACH"
        else "Standard Operating Procedure (SOP) verified"
    )
    details = f"Query: '{query_text[:80]}' | Results: {result_count} | {latency_ms:.1f}ms"
    log_quality_event(
        module=module,
        action=action,
        status=status,
        latency_ms=latency_ms,
        details=details,
        remedial_action=remedial,
    )


def _timed(fn, *args, **kwargs) -> Tuple[Any, float]:
    """Runs fn(*args, **kwargs) and returns (result, elapsed_ms)."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, (time.perf_counter() - t0) * 1000.0


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — GLOBAL QUICK SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def quick_search(
    query: str,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Instant multi-entity search: books (title/author/ISBN/category)
    and members (name/USN).
    Returns a unified result dict with matched books, members and timing KPI.
    """
    q = (query or "").strip()
    if not q:
        return {
            "books": [], "members": [],
            "total": 0, "query": q,
            "latency_ms": 0.0, "sla_ok": True,
        }

    t0 = time.perf_counter()

    with get_db() as db:
        pattern = f"%{q}%"

        # Book search — uses idx_book_search, idx_book_isbn
        book_rows = db.scalars(
            select(Book).where(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.isbn.ilike(pattern),
                    Book.category.ilike(pattern),
                    Book.shelf_location.ilike(pattern),
                )
            ).limit(limit)
        ).all()

        # Member search — uses idx_member_usn
        member_rows = db.scalars(
            select(Member).where(
                or_(
                    Member.name.ilike(pattern),
                    Member.usn.ilike(pattern),
                    Member.email.ilike(pattern),
                    Member.department.ilike(pattern),
                )
            ).limit(limit)
        ).all()

        books = [b.to_dict() for b in book_rows]
        members = [m.to_dict() for m in member_rows]

    latency_ms = (time.perf_counter() - t0) * 1000.0

    _record_search_kpi("CATALOG", "QUICK_SEARCH", latency_ms,
                       len(books) + len(members), q)

    return {
        "books":           books,
        "matched_books":   books,
        "members":         members,
        "matched_members": members,
        "total":           len(books) + len(members),
        "query":           q,
        "latency_ms":      round(latency_ms, 2),
        "sla_ok":          latency_ms <= SLA_MS,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — ADVANCED BOOK SEARCH WITH FILTERS, SORT & PAGINATION
# ══════════════════════════════════════════════════════════════════════════════

def search_books(
    query: str = "",
    category: str = "",
    availability: str = "",       # "Available" | "Unavailable" | ""
    sort_by: str = "title",       # title | author | category | year | available_copies
    sort_dir: str = "asc",        # asc | desc
    page: int = 1,
    page_size: int = 20,
    per_page: Optional[int] = None,
    available_only: Optional[bool] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Advanced filtered, sorted, paginated book search.
    Measures and records response time against the 100 ms SLA.
    """
    t0 = time.perf_counter()
    page = max(1, page)
    if per_page is not None:
        page_size = per_page
    if available_only is True:
        availability = "Available"

    with get_db() as db:
        stmt = select(Book)

        if query.strip():
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.isbn.ilike(pattern),
                    Book.category.ilike(pattern),
                )
            )
        if category and category not in ("All", ""):
            stmt = stmt.where(Book.category == category)
        if availability == "Available":
            stmt = stmt.where(Book.available_copies > 0)
        elif availability == "Unavailable":
            stmt = stmt.where(Book.available_copies == 0)

        # Count total matching rows for pagination metadata
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Sorting
        _sort_cols = {
            "title":            Book.title,
            "author":           Book.author,
            "category":         Book.category,
            "year":             Book.year,
            "available_copies": Book.available_copies,
            "isbn":             Book.isbn,
        }
        col = _sort_cols.get(sort_by, Book.title)
        stmt = stmt.order_by(asc(col) if sort_dir == "asc" else desc(col))

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        books = db.scalars(stmt).all()
        results = [b.to_dict() for b in books]

    latency_ms = (time.perf_counter() - t0) * 1000.0
    _record_search_kpi("CATALOG", "BOOK_SEARCH", latency_ms, total, query)

    return {
        "results":    results,
        "books":      results,
        "total":      total,
        "page":       page,
        "page_size":  page_size,
        "pages":      max(1, -(-total // page_size)),   # ceiling division
        "query":      query,
        "latency_ms": round(latency_ms, 2),
        "sla_ok":     latency_ms <= SLA_MS,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — ADVANCED MEMBER SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def search_members(
    query: str = "",
    department: str = "",
    status: str = "",
    membership_type: str = "",
    sort_by: str = "name",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 20,
    per_page: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Advanced filtered, sorted, paginated member search.
    """
    t0 = time.perf_counter()
    page = max(1, page)
    if per_page is not None:
        page_size = per_page

    with get_db() as db:
        stmt = select(Member)

        if query.strip():
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Member.name.ilike(pattern),
                    Member.usn.ilike(pattern),
                    Member.email.ilike(pattern),
                    Member.phone.ilike(pattern),
                )
            )
        if department and department not in ("All", ""):
            stmt = stmt.where(Member.department == department)
        if status and status not in ("All", ""):
            stmt = stmt.where(Member.status == status)
        if membership_type and membership_type not in ("All", ""):
            stmt = stmt.where(Member.membership_type == membership_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        _sort_cols = {
            "name":       Member.name,
            "usn":        Member.usn,
            "department": Member.department,
            "semester":   Member.semester,
            "status":     Member.status,
        }
        col = _sort_cols.get(sort_by, Member.name)
        stmt = stmt.order_by(asc(col) if sort_dir == "asc" else desc(col))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        members = db.scalars(stmt).all()
        results = [m.to_dict() for m in members]

    latency_ms = (time.perf_counter() - t0) * 1000.0
    _record_search_kpi("MEMBER", "MEMBER_SEARCH", latency_ms, total, query)

    return {
        "results":    results,
        "members":    results,
        "total":      total,
        "page":       page,
        "page_size":  page_size,
        "pages":      max(1, -(-total // page_size)),
        "query":      query,
        "latency_ms": round(latency_ms, 2),
        "sla_ok":     latency_ms <= SLA_MS,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — LOAN SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def search_loans(
    query: str = "",
    status: str = "",
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = "borrow_date",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Searches circulation/loan records with optional filters:
    text (book title / member name / USN), status, and date range.
    """
    t0 = time.perf_counter()
    page = max(1, page)

    with get_db() as db:
        stmt = select(Loan).join(Book, Loan.book_id == Book.id).join(Member, Loan.member_id == Member.id)

        if query.strip():
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Book.title.ilike(pattern),
                    Member.name.ilike(pattern),
                    Member.usn.ilike(pattern),
                )
            )
        if status and status not in ("All", ""):
            stmt = stmt.where(Loan.status == status)
        if date_from:
            stmt = stmt.where(Loan.borrow_date >= date_from)
        if date_to:
            stmt = stmt.where(Loan.borrow_date <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        _sort_cols = {
            "borrow_date": Loan.borrow_date,
            "due_date":    Loan.due_date,
            "status":      Loan.status,
            "fine_amount": Loan.fine_amount,
        }
        col = _sort_cols.get(sort_by, Loan.borrow_date)
        stmt = stmt.order_by(asc(col) if sort_dir == "asc" else desc(col))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        loans = db.scalars(stmt).all()
        results = [l.to_dict() for l in loans]

    latency_ms = (time.perf_counter() - t0) * 1000.0
    _record_search_kpi("CIRCULATION", "LOAN_SEARCH", latency_ms, total, query)

    return {
        "results":    results,
        "loans":      results,
        "total":      total,
        "page":       page,
        "page_size":  page_size,
        "pages":      max(1, -(-total // page_size)),
        "query":      query,
        "latency_ms": round(latency_ms, 2),
        "sla_ok":     latency_ms <= SLA_MS,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — SEARCH KPI ANALYTICS (for Dashboard)
# ══════════════════════════════════════════════════════════════════════════════

def get_search_kpi_summary(limit: int = 100) -> Dict[str, Any]:
    """
    Aggregates recent search performance data from QualityLog for the KPI dashboard.
    Returns avg latency, SLA pass rate, and the last N search events.
    """
    with get_db() as db:
        search_actions = ["QUICK_SEARCH", "BOOK_SEARCH", "MEMBER_SEARCH", "LOAN_SEARCH"]
        recent = db.scalars(
            select(QualityLog)
            .where(QualityLog.action.in_(search_actions))
            .order_by(desc(QualityLog.timestamp))
            .limit(limit)
        ).all()

        if not recent:
            return {
                "avg_latency_ms": 0.0,
                "sla_pass_rate": 100.0,
                "total_searches": 0,
                "sla_breaches": 0,
                "recent": [],
            }

        latencies   = [r.execution_time_ms for r in recent]
        breaches    = [r for r in recent if r.status == "SLA_BREACH"]
        avg_latency = round(sum(latencies) / len(latencies), 2)
        sla_pass    = round((1 - len(breaches) / len(recent)) * 100, 1)

        return {
            "avg_latency_ms": avg_latency,
            "sla_pass_rate":  sla_pass,
            "total_searches": len(recent),
            "sla_breaches":   len(breaches),
            "recent": [r.to_dict() for r in recent[:20]],
        }
