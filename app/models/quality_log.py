from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

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
    module: Mapped[str] = mapped_column(String(50), nullable=False)  # CIRCULATION, CATALOG, PAYROLL, DATABASE
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS")  # SUCCESS, DEFECT, WARNING, SLA_BREACH
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)  # Latency monitoring for DB optimization
    details: Mapped[str] = mapped_column(String(255), default="")
    remedial_action: Mapped[str] = mapped_column(String(255), default="Standard Operating Procedure (SOP) verified")

    def __repr__(self) -> str:
        return f"<QualityLog id={self.id} Module='{self.module}' Status='{self.status}' Latency={self.execution_time_ms}ms>"
