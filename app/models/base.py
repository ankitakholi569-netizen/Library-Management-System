from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
from app.config import DATABASE_URL
from app.core.logger import get_logger

logger = get_logger("database")

# Initialize SQLite Engine with Foreign Key Enforcement
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for verbose SQL query logging
)

# SQLite foreign key constraint enforcement listener
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for high concurrency & speed
    cursor.close()

# Scoped Thread-Safe Session Factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine))

class Base(DeclarativeBase):
    """Base declarative class for all TQM ORM models."""
    pass

@contextmanager
def get_db():
    """
    Context manager for database sessions with automatic commit/rollback.
    Demonstrates TQM Principle: Error Prevention & Data Consistency.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Database transaction rollback due to error: {exc}")
        raise
    finally:
        session.close()
