from datetime import date, datetime
from sqlalchemy import Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.config import TQM_CONFIG

class Loan(Base):
    """
    Circulation & Borrow Record with SLA Quality Tracking.
    Demonstrates TQM Principle: Process Automation & Accuracy.
    """
    __tablename__ = "loans"
    __table_args__ = (
        Index("idx_loan_status_dates", "status", "due_date"),
        Index("idx_loan_book_member", "book_id", "member_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    
    issue_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="Borrowed", nullable=False)  # Borrowed, Returned, Overdue
    fine_amount: Mapped[float] = mapped_column(Float, default=0.0)
    fine_paid: Mapped[bool] = mapped_column(Integer, default=False)
    
    processed_by: Mapped[str] = mapped_column(String(50), default="Librarian")

    # Relationships
    book = relationship("Book", back_populates="loans")
    member = relationship("Member", back_populates="loans")

    def check_and_update_overdue(self, as_of: date | None = None) -> float:
        """
        Automated calculation of overdue days and fine.
        Demonstrates TQM Process Automation.
        """
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

    def days_overdue(self, as_of: date | None = None) -> int:
        target_date = as_of or (self.return_date if self.return_date else date.today())
        if target_date > self.due_date:
            return (target_date - self.due_date).days
        return 0

    def __repr__(self) -> str:
        return f"<Loan id={self.id} BookID={self.book_id} MemberID={self.member_id} Status='{self.status}'>"
