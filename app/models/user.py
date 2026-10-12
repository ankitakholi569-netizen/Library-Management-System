from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.core.security import hash_password, verify_password

class User(Base):
    """
    Staff and Administrator User accounts.
    Demonstrates TQM Principle: Role Standardization & Access Security.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="Librarian", nullable=False)  # Chief Librarian, Assistant Librarian, Library Assistant
    email: Mapped[str] = mapped_column(String(120), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    shifts = relationship("StaffShift", back_populates="user", cascade="all, delete-orphan")
    payrolls = relationship("StaffPayroll", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password_text: str):
        """Hashes and sets the user's password."""
        self.hashed_password = hash_password(password_text)

    def verify_password(self, password_text: str) -> bool:
        """Verifies plain password against hashed value."""
        return verify_password(password_text, self.hashed_password)

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}' role='{self.role}'>"
