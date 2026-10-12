from sqlalchemy import Integer, String, Boolean, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Book(Base):
    """
    Cataloged Textbook & Inventory Record.
    Demonstrates TQM Principle: Quality Monitoring & Defect Prevention.
    """
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("available_copies >= 0", name="chk_available_positive"),
        CheckConstraint("total_copies >= available_copies", name="chk_copies_consistency"),
        Index("idx_book_search", "title", "author", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), default="General", index=True)
    isbn: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, default=2024)
    total_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # TQM Inspection Fields
    defect_flag: Mapped[bool] = mapped_column(Boolean, default=False)  # Damaged / Missing pages
    defect_notes: Mapped[str] = mapped_column(String(255), default="")

    # Relationships
    loans = relationship("Loan", back_populates="book", cascade="all, delete-orphan")

    def borrow_copy(self) -> bool:
        """Decrements available copies safely. Returns False if out of stock."""
        if self.available_copies > 0:
            self.available_copies -= 1
            return True
        return False

    def return_copy(self) -> bool:
        """Increments available copies safely up to total copies."""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            return True
        return False

    def __repr__(self) -> str:
        return f"<Book id={self.id} ISBN='{self.isbn}' Title='{self.title}'>"
