from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.config import TQM_CONFIG

class Member(Base):
    """
    Student & Faculty Library Patrons.
    Demonstrates TQM Principle: Customer Focus & Data Accuracy.
    """
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usn: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(50), default="CSE", index=True)
    semester: Mapped[int] = mapped_column(Integer, default=1)
    email: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(20), default="Active")  # Active, Suspended
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    loans = relationship("Loan", back_populates="member", cascade="all, delete-orphan")

    def active_loans(self):
        """Returns non-returned active loan records."""
        return [loan for loan in self.loans if loan.status in ("Borrowed", "Overdue")]

    def can_borrow(self) -> tuple[bool, str]:
        """
        Validates loan eligibility against TQM limits.
        Demonstrates TQM Error Prevention.
        """
        if self.status != "Active":
            return False, "Member status is suspended. Cannot issue books."
        active_count = len(self.active_loans())
        max_allowed = TQM_CONFIG["MAX_BOOKS_PER_MEMBER"]
        if active_count >= max_allowed:
            return False, f"Maximum quota reached ({active_count}/{max_allowed} books currently issued)."
        return True, "Eligible to borrow."

    def __repr__(self) -> str:
        return f"<Member USN='{self.usn}' Name='{self.name}' Dept='{self.department}'>"
