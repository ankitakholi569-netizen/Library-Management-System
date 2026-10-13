from datetime import date, datetime
from sqlalchemy import Integer, String, Float, Date, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.config import TQM_CONFIG

class StaffShift(Base):
    """
    Staff work shift log for automated payroll computation.
    Demonstrates TQM Principle: Automation & Performance Measurement.
    """
    __tablename__ = "staff_shifts"
    __table_args__ = (
        Index("idx_shift_user_date", "user_id", "shift_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    shift_type: Mapped[str] = mapped_column(String(30), default="Regular Day Shift")  # Morning, Evening, Circulation Desk
    regular_hours: Mapped[float] = mapped_column(Float, default=8.0)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    tasks_completed: Mapped[str] = mapped_column(String(255), default="Catalog maintenance & desk circulation")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="shifts")

    def total_hours(self) -> float:
        return self.regular_hours + self.overtime_hours

    def __repr__(self) -> str:
        return f"<StaffShift id={self.id} UserID={self.user_id} Date={self.shift_date} Hours={self.total_hours()}>"


class StaffPayroll(Base):
    """
    Automated monthly payroll summary calculated from verified shifts.
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
    
    regular_amount: Mapped[float] = mapped_column(Float, default=0.0)
    overtime_amount: Mapped[float] = mapped_column(Float, default=0.0)
    gross_salary: Mapped[float] = mapped_column(Float, default=0.0)
    deductions: Mapped[float] = mapped_column(Float, default=0.0)
    net_salary: Mapped[float] = mapped_column(Float, default=0.0)
    
    status: Mapped[str] = mapped_column(String(20), default="Processed")  # Processed, Approved, Disbursed
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payrolls")

    def compute(self, rate: float | None = None, deduction_rate: float | None = None):
        """
        Standardized automated calculation formula.
        Gross = (Reg_Hours * Rate) + (OT_Hours * Rate * OT_Multiplier)
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

    def __repr__(self) -> str:
        return f"<StaffPayroll id={self.id} UserID={self.user_id} Period={self.period_month}/{self.period_year} Net={self.net_salary}>"
