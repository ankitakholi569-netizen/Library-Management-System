"""
SQLAlchemy ORM Models for Library Management System (TQM Edition).
Course: BBAT104.
Demonstrates TQM Principles:
- Standardization of records
- Search & Retrieval Optimization (Strategic B-Tree Indexes)
- Data Consistency & Referential Integrity (Foreign Keys & Check Constraints)
- Traceability (QualityLog Audit Trail)
"""

from datetime import date, datetime
from typing import Optional
import bcrypt
from sqlalchemy import (
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db import Base
from config.settings import TQM_CONFIG, BCRYPT_ROUNDS


# ==============================================================================
# 1. USER & AUTHENTICATION MODEL
# ==============================================================================
class User(Base):
    """
    Staff, Administrators, and System Operators.
    Standardized access control aligning with TQM security governance.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_role", "role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="Librarian", nullable=False)
    email: Mapped[str] = mapped_column(String(120), default="")
    department: Mapped[str] = mapped_column(String(60), default="Library Administration")
    hourly_rate: Mapped[float] = mapped_column(Float, default=TQM_CONFIG["HOURLY_PAY_RATE"])
    base_salary: Mapped[float] = mapped_column(Float, default=24000.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    shifts = relationship("StaffShift", back_populates="user", cascade="all, delete-orphan")
    payrolls = relationship("StaffPayroll", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password_text: str):
        """Hashes password with bcrypt and salt rounds."""
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        self.hashed_password = bcrypt.hashpw(password_text.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password_text: str) -> bool:
        """Verifies plain password against stored bcrypt hash."""
        try:
            return bcrypt.checkpw(
                password_text.encode("utf-8"),
                self.hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "email": self.email,
            "department": self.department,
            "hourly_rate": self.hourly_rate,
            "base_salary": self.base_salary,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}' role='{self.role}'>"


# ==============================================================================
# 2. BOOK CATALOG & INVENTORY MODEL
# ==============================================================================
class Book(Base):
    """
    Textbook & Library Inventory Record.
    Demonstrates TQM Defect Prevention & Optimized Search Retrieval.
    """
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("available_copies >= 0", name="chk_available_positive"),
        CheckConstraint("total_copies >= available_copies", name="chk_copies_consistency"),
        Index("idx_book_search", "title", "author", "category", "shelf_location"),
        Index("idx_book_isbn", "isbn"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), default="General", index=True)
    isbn: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, default=2024)
    total_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    shelf_location: Mapped[str] = mapped_column(String(60), default="Aisle 1 - Rack A", nullable=False)

    # TQM Inspection Fields
    defect_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    defect_notes: Mapped[str] = mapped_column(String(255), default="")

    # Relationships
    loans = relationship("Loan", back_populates="book", cascade="all, delete-orphan")

    @property
    def book_id(self) -> int:
        return self.id

    def borrow_copy(self) -> bool:
        """Safely decrements available copies."""
        if self.available_copies > 0:
            self.available_copies -= 1
            return True
        return False

    def return_copy(self) -> bool:
        """Safely increments available copies up to total copies."""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "isbn": self.isbn,
            "year": self.year,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "shelf_location": self.shelf_location,
            "defect_flag": self.defect_flag,
            "defect_notes": self.defect_notes,
        }

    def __repr__(self) -> str:
        return f"<Book id={self.id} ISBN='{self.isbn}' Title='{self.title[:30]}'>"


# ==============================================================================
# 3. MEMBER & PATRON MODEL
# ==============================================================================
class Member(Base):
    """
    Student, Scholar & Faculty Library Patrons.
    Demonstrates TQM Customer Focus, Quota Validation & Fast Indexing.
    """
    __tablename__ = "members"
    __table_args__ = (
        Index("idx_member_usn", "usn"),
        Index("idx_member_dept", "department"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usn: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(50), default="CSE", index=True)
    semester: Mapped[int] = mapped_column(Integer, default=1)
    membership_type: Mapped[str] = mapped_column(String(50), default="Student", nullable=False)
    email: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(20), default="Active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    loans = relationship("Loan", back_populates="member", cascade="all, delete-orphan", lazy="selectin")

    @property
    def member_id(self) -> int:
        return self.id

    @property
    def full_name(self) -> str:
        return self.name

    @property
    def joined_date(self) -> datetime:
        return self.created_at

    @property
    def is_active(self) -> bool:
        return self.status == "Active"

    def active_loans(self) -> list:
        try:
            return [loan for loan in self.loans if loan.status in ("Borrowed", "Overdue")]
        except Exception:
            return []

    def can_borrow(self) -> tuple[bool, str]:
        """TQM Error Prevention: Validates member borrowing eligibility."""
        if self.status != "Active":
            return False, "Member status is suspended. Cannot issue books."
        active_count = len(self.active_loans())
        max_allowed = TQM_CONFIG["MAX_BOOKS_PER_MEMBER"]
        if active_count >= max_allowed:
            return False, f"Maximum quota reached ({active_count}/{max_allowed} books currently issued)."
        return True, "Eligible to borrow."

    def to_dict(self) -> dict:
        try:
            active_count = len(self.active_loans())
        except Exception:
            active_count = 0
        return {
            "id": self.id,
            "member_id": self.id,
            "usn": self.usn,
            "name": self.name,
            "department": self.department,
            "semester": self.semester,
            "membership_type": self.membership_type,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "active_loans": active_count,
            "borrowed_count": active_count,
            "max_books": TQM_CONFIG.get("MAX_BOOKS_PER_MEMBER", 3),
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
        }

    def __repr__(self) -> str:
        return f"<Member ID={self.id} USN='{self.usn}' Name='{self.name}'>"


# ==============================================================================
# 4. CIRCULATION & LOAN MODEL
# ==============================================================================
class Loan(Base):
    """
    Circulation Transactions Record.
    Demonstrates TQM SLA Due Date Compliance & Automated Fine Calculation.
    """
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_txn_status_dates", "status", "due_date"),
        Index("idx_txn_book_member", "book_id", "member_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)

    borrow_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="Borrowed", nullable=False)  # Borrowed, Returned, Overdue
    fine_amount: Mapped[float] = mapped_column(Float, default=0.0)
    fine_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_by: Mapped[str] = mapped_column(String(50), default="Librarian")

    # Relationships
    book = relationship("Book", back_populates="loans")
    member = relationship("Member", back_populates="loans")

    @property
    def transaction_id(self) -> int:
        return self.id

    @property
    def issue_date(self) -> date:
        return self.borrow_date

    @issue_date.setter
    def issue_date(self, value: date):
        self.borrow_date = value

    def check_and_update_overdue(self, as_of: Optional[date] = None) -> float:
        """Automated calculation of overdue days and SLA fine."""
        target_date = as_of or date.today()
        if self.status != "Returned":
            if target_date > self.due_date:
                overdue_days = (target_date - self.due_date).days
                self.status = "Overdue"
                self.fine_amount = round(overdue_days * TQM_CONFIG["FINE_PER_DAY"], 2)
            else:
                self.status = "Borrowed"
                self.fine_amount = 0.0
        return self.fine_amount

    def days_overdue(self, as_of: Optional[date] = None) -> int:
        target_date = as_of or (self.return_date if self.return_date else date.today())
        if target_date > self.due_date:
            return (target_date - self.due_date).days
        return 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "transaction_id": self.id,
            "book_id": self.book_id,
            "book_title": self.book.title if self.book else "",
            "member_id": self.member_id,
            "member_name": self.member.name if self.member else "",
            "member_usn": self.member.usn if self.member else "",
            "borrow_date": self.borrow_date.strftime("%Y-%m-%d"),
            "due_date": self.due_date.strftime("%Y-%m-%d"),
            "return_date": self.return_date.strftime("%Y-%m-%d") if self.return_date else None,
            "status": self.status,
            "fine_amount": self.fine_amount,
            "fine_paid": self.fine_paid,
            "processed_by": self.processed_by,
        }

    def __repr__(self) -> str:
        return f"<Loan id={self.id} BookID={self.book_id} MemberID={self.member_id} Status='{self.status}'>"

# Alias for compatibility
Transaction = Loan


# ==============================================================================
# 5. STAFF SHIFT LOGS MODEL (TQM Performance Tracking)
# ==============================================================================
class StaffShift(Base):
    """
    Staff work shift log for automated payroll computation.
    Demonstrates TQM Principle: Automation & Objective Performance Measurement.
    """
    __tablename__ = "staff_shifts"
    __table_args__ = (
        Index("idx_shift_user_date", "user_id", "shift_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    shift_type: Mapped[str] = mapped_column(String(30), default="Regular Day Shift")
    regular_hours: Mapped[float] = mapped_column(Float, default=8.0)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    tasks_completed: Mapped[str] = mapped_column(String(255), default="Catalog maintenance & desk circulation")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="shifts")

    def total_hours(self) -> float:
        return self.regular_hours + self.overtime_hours

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "staff_name": self.user.full_name if self.user else "",
            "shift_date": self.shift_date.strftime("%Y-%m-%d"),
            "shift_type": self.shift_type,
            "regular_hours": self.regular_hours,
            "overtime_hours": self.overtime_hours,
            "total_hours": self.total_hours(),
            "tasks_completed": self.tasks_completed,
            "is_verified": self.is_verified,
        }

    def __repr__(self) -> str:
        return f"<StaffShift id={self.id} UserID={self.user_id} Date={self.shift_date} Hours={self.total_hours()}>"


# ==============================================================================
# 6. STAFF PAYROLL MODEL (TQM Automated Processing)
# ==============================================================================
class StaffPayroll(Base):
    """
    Automated monthly payroll summary calculated from verified operational shifts.
    Demonstrates TQM Principle: Error Reduction & Standardized Calculation.
    """
    __tablename__ = "staff_payrolls"
    __table_args__ = (
        Index("idx_payroll_user_period", "user_id", "period_month", "period_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)

    total_regular_hours: Mapped[float] = mapped_column(Float, default=0.0)
    total_overtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    hourly_rate: Mapped[float] = mapped_column(Float, default=TQM_CONFIG["HOURLY_PAY_RATE"])

    base_salary: Mapped[float] = mapped_column(Float, default=22000.0)
    performance_rating: Mapped[float] = mapped_column(Float, default=4.8)  # Out of 5.0 (TQM quality score)

    regular_amount: Mapped[float] = mapped_column(Float, default=0.0)
    overtime_amount: Mapped[float] = mapped_column(Float, default=0.0)
    gross_salary: Mapped[float] = mapped_column(Float, default=0.0)
    deductions: Mapped[float] = mapped_column(Float, default=0.0)
    net_salary: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[str] = mapped_column(String(20), default="Processed")  # Processed, Approved, Disbursed
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payrolls")

    @property
    def staff_id(self) -> int:
        return self.user_id

    @property
    def name(self) -> str:
        return self.user.full_name if self.user else ""

    @property
    def role(self) -> str:
        return self.user.role if self.user else ""

    def compute(self, rate: Optional[float] = None, deduction_rate: Optional[float] = None):
        """
        Standardized automated calculation formula.
        Gross = (Reg_Hours * Rate) + (OT_Hours * Rate * OT_Multiplier)
        Net = Gross - Deductions
        """
        hourly = rate if rate is not None else self.hourly_rate
        d_rate = deduction_rate if deduction_rate is not None else TQM_CONFIG["TAX_DEDUCTION_RATE"]
        ot_mult = TQM_CONFIG["OVERTIME_MULTIPLIER"]

        self.hourly_rate = hourly
        self.regular_amount = round(self.total_regular_hours * hourly, 2)
        self.overtime_amount = round(self.total_overtime_hours * hourly * ot_mult, 2)
        self.gross_salary = round(self.regular_amount + self.overtime_amount, 2)
        self.deductions = round(self.gross_salary * d_rate, 2)
        self.net_salary = round(self.gross_salary - self.deductions, 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "staff_id": self.user_id,
            "staff_name": self.name,
            "role": self.role,
            "period": f"{self.period_month:02d}/{self.period_year}",
            "period_month": self.period_month,
            "period_year": self.period_year,
            "total_regular_hours": self.total_regular_hours,
            "total_overtime_hours": self.total_overtime_hours,
            "hourly_rate": self.hourly_rate,
            "regular_amount": self.regular_amount,
            "overtime_amount": self.overtime_amount,
            "gross_salary": self.gross_salary,
            "deductions": self.deductions,
            "net_salary": self.net_salary,
            "performance_rating": self.performance_rating,
            "status": self.status,
            "processed_at": self.processed_at.strftime("%Y-%m-%d %H:%M:%S") if self.processed_at else "",
        }

    def __repr__(self) -> str:
        return f"<StaffPayroll id={self.id} StaffID={self.user_id} Rating={self.performance_rating} Net={self.net_salary}>"


# ==============================================================================
# 7. TQM QUALITY & PERFORMANCE LOG MODEL (Continuous Improvement)
# ==============================================================================
class QualityLog(Base):
    """
    TQM Quality Monitoring & Continuous Improvement Ledger.
    Records system operation times, SLAs, defect occurrences, and corrective actions.
    Demonstrates TQM Principle: Quality Monitoring & Continuous Improvement.
    """
    __tablename__ = "quality_logs"
    __table_args__ = (
        Index("idx_quality_timestamp_status", "timestamp", "status"),
        Index("idx_quality_module", "module"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)  # CIRCULATION, CATALOG, PAYROLL, DATABASE, AUTH
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS")  # SUCCESS, DEFECT, WARNING, SLA_BREACH
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)  # Latency monitoring for DB optimization
    details: Mapped[str] = mapped_column(String(255), default="")
    remedial_action: Mapped[str] = mapped_column(String(255), default="Standard Operating Procedure (SOP) verified")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "module": self.module,
            "action": self.action,
            "status": self.status,
            "execution_time_ms": self.execution_time_ms,
            "details": self.details,
            "remedial_action": self.remedial_action,
        }

    def __repr__(self) -> str:
        return f"<QualityLog id={self.id} Module='{self.module}' Status='{self.status}' Latency={self.execution_time_ms}ms>"
